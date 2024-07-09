import json
import os
import pickle
import random
import warnings

import numpy as np
import pytest

from audiomentations import AddBackgroundNoise, Compose, Reverse
from demo.demo import DEMO_DIR


def test_add_background_noise():
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 22500)).astype(np.float32)
    sample_rate = 44100
    augmenter = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "background_noises"),
        min_snr_db=15.0,
        max_snr_db=35.0,
        p=1.0,
    )
    samples_out = augmenter(samples=samples, sample_rate=sample_rate)
    assert not np.allclose(samples, samples_out)
    assert samples_out.dtype == np.float32

    # test old API
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 22500)).astype(np.float32)
    sample_rate = 44100
    with pytest.warns(DeprecationWarning):
        augmenter = AddBackgroundNoise(
            sounds_path=os.path.join(DEMO_DIR, "background_noises"),
            min_snr_in_db=15,
            max_snr_in_db=35,
            p=1.0,
        )
    samples_out = augmenter(samples=samples, sample_rate=sample_rate)
    assert not np.allclose(samples, samples_out)
    assert samples_out.dtype == np.float32


def test_pass_both_old_and_new_args():
    with pytest.raises(ValueError):
        AddBackgroundNoise(
            sounds_path=os.path.join(DEMO_DIR, "background_noises"),
            min_snr_db=15,
            max_snr_db=35,
            min_snr_in_db=15,
            max_snr_in_db=35,
        )


def test_add_background_noise_when_noise_sound_is_too_short():
    sample_rate = 44100
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 14 * sample_rate)).astype(
        np.float32
    )
    augmenter = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "background_noises"),
        min_snr_db=15,
        max_snr_db=35,
        p=1.0,
    )
    samples_out = augmenter(samples=samples, sample_rate=sample_rate)
    assert not np.allclose(samples, samples_out)
    assert samples_out.dtype == np.float32


def test_try_add_almost_silent_file():
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 30000)).astype(np.float32)
    sample_rate = 48000
    augmenter = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "almost_silent"),
        min_snr_db=15,
        max_snr_db=35,
        p=1.0,
    )
    samples_out = augmenter(samples=samples, sample_rate=sample_rate)
    assert not np.allclose(samples, samples_out)
    assert samples_out.dtype == np.float32


def test_try_add_digital_silence():
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 40000)).astype(np.float32)
    sample_rate = 48000
    augmenter = Compose([
        AddBackgroundNoise(
            sounds_path=os.path.join(DEMO_DIR, "digital_silence"),
            min_snr_db=15,
            max_snr_db=35,
            p=1.0,
        )
    ])

    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")
        samples_out = augmenter(samples=samples, sample_rate=sample_rate)

        assert "is too silent to be added as noise" in str(w[-1].message)

    assert np.allclose(samples, samples_out)
    assert samples_out.dtype == np.float32


def test_serialize_parameters():
    transform = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "background_noises"), p=1.0
    )
    samples = np.random.normal(0, 1, size=1024).astype(np.float32)
    transform.randomize_parameters(samples, sample_rate=44100)
    json.dumps(transform.serialize_parameters())


def test_picklability():
    transform = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "background_noises"), p=1.0
    )
    pickled = pickle.dumps(transform)
    unpickled = pickle.loads(pickled)
    assert transform.sound_file_paths == unpickled.sound_file_paths


def test_absolute_option():
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 22500)).astype(np.float32)
    sample_rate = 44100
    augmenter = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "background_noises"),
        noise_rms="absolute",
        p=1.0,
    )
    samples_out = augmenter(samples=samples, sample_rate=sample_rate)
    assert not np.allclose(samples, samples_out)


def test_noise_transform():
    np.random.seed(3650)
    random.seed(3650)
    samples = np.sin(np.linspace(0, 440 * 2 * np.pi, 22500)).astype(np.float32)
    sample_rate = 44100
    augmenter = AddBackgroundNoise(
        sounds_path=os.path.join(DEMO_DIR, "background_noises"),
        min_snr_db=3,
        max_snr_db=6,
        p=1.0,
    )
    samples_out_without_transform = augmenter(samples=samples, sample_rate=sample_rate)
    augmenter.freeze_parameters()
    augmenter.noise_transform = Reverse()
    samples_out_with_transform = augmenter(samples=samples, sample_rate=sample_rate)

    assert not np.allclose(samples_out_without_transform, samples_out_with_transform)
