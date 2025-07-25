import os

from trainer import Trainer, TrainerArgs

from TTS.config.shared_configs import BaseAudioConfig
from TTS.tts.configs.shared_configs import BaseDatasetConfig
from TTS.tts.configs.tacotron2_config import Tacotron2Config
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.tacotron2 import Tacotron2
from TTS.tts.utils.speakers import SpeakerManager
from TTS.tts.utils.text.tokenizer import TTSTokenizer
from TTS.utils.audio import AudioProcessor

output_path = os.path.dirname(os.path.abspath(__file__))
dataset_config = BaseDatasetConfig(formatter="vctk", meta_file_train="", path=os.path.join(output_path, "../VCTK/"))

audio_config = BaseAudioConfig(
    sample_rate=22050,
    resample=False,  # Resample to 22050 Hz. It slows down training. Use `TTS/bin/resample.py` to pre-resample and set this False for faster training.
    do_trim_silence=True,
    trim_db=23.0,
    signal_norm=False,
    mel_fmin=0.0,
    mel_fmax=8000,
    spec_gain=1.0,
    log_func="np.log",
    preemphasis=0.0,
)

config = Tacotron2Config(  # This is the config that is saved for the future use
    audio=audio_config,
    batch_size=32,
    eval_batch_size=16,
    num_loader_workers=4,
    num_eval_loader_workers=4,
    run_eval=True,
    test_delay_epochs=-1,
    r=2,
    # gradual_training=[[0, 6, 48], [10000, 4, 32], [50000, 3, 32], [100000, 2, 32]],
    double_decoder_consistency=False,
    epochs=300,
    text_cleaner="phoneme_cleaners",
    use_phonemes=True,
    phoneme_language="en-us",
    phoneme_cache_path=os.path.join(output_path, "phoneme_cache"),
    print_step=150,
    print_eval=False,
    mixed_precision=True,
    min_text_len=0,
    max_text_len=500,
    min_audio_len=0,
    max_audio_len=44000 * 10,
    output_path=output_path,
    datasets=[dataset_config],
    use_speaker_embedding=True,  # set this to enable multi-sepeaker training
    decoder_ssim_alpha=0.0,  # disable ssim losses that causes NaN for some runs.
    postnet_ssim_alpha=0.0,
    postnet_diff_spec_alpha=0.0,
    decoder_diff_spec_alpha=0.0,
    attention_norm="softmax",
    optimizer="Adam",
    lr_scheduler=None,
    lr=3e-5,
)

## INITIALIZE THE AUDIO PROCESSOR
# Audio processor is used for feature extraction and audio I/O.
# It mainly serves to the dataloader and the training loggers.
ap = AudioProcessor.init_from_config(config)

# INITIALIZE THE TOKENIZER
# Tokenizer is used to convert text to sequences of token IDs.
# If characters are not defined in the config, default characters are passed to the config
tokenizer, config = TTSTokenizer.init_from_config(config)

# LOAD DATA SAMPLES
# Each sample is a list of ```[text, audio_file_path, speaker_name]```
# You can define your custom sample loader returning the list of samples.
# Or define your custom formatter and pass it to the `load_tts_samples`.
# Check `TTS.tts.datasets.load_tts_samples` for more details.
train_samples, eval_samples = load_tts_samples(
    dataset_config,
    eval_split=True,
    eval_split_max_size=config.eval_split_max_size,
    eval_split_size=config.eval_split_size,
)

# init speaker manager for multi-speaker training
# it mainly handles speaker-id to speaker-name for the model and the data-loader
speaker_manager = SpeakerManager()
speaker_manager.set_ids_from_data(train_samples + eval_samples, parse_key="speaker_name")

# init model
model = Tacotron2(config, ap, tokenizer, speaker_manager)

# INITIALIZE THE TRAINER
# Trainer provides a generic API to train all the 🐸TTS models with all its perks like mixed-precision training,
# distributed training, etc.
trainer = Trainer(
    TrainerArgs(), config, output_path, model=model, train_samples=train_samples, eval_samples=eval_samples
)

# AND... 3,2,1... 🚀
trainer.fit()
