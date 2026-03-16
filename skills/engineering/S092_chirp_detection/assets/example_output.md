{
  "detections": [
    {
      "start_time": 45,
      "end_time": 54,
      "start_frequency": 128,
      "end_frequency": 156,
      "confidence": 0.742
    },
    {
      "start_time": 78,
      "end_time": 87,
      "start_frequency": 200,
      "end_frequency": 175,
      "confidence": 0.689
    },
    {
      "start_time": 120,
      "end_time": 129,
      "start_frequency": 90,
      "end_frequency": 115,
      "confidence": 0.823
    }
  ],
  "statistics": {
    "total_chirps": 3,
    "average_confidence": 0.751,
    "candidates_evaluated": 47
  }
}

Console Output:
INFO:__main__:Loading spectrogram from radar_data.npy
INFO:__main__:Spectrogram shape: (512, 1024)
INFO:__main__:Data range: -45.230 to 12.450
INFO:__main__:Processing 204 windows...
INFO:__main__:Candidate 1: R²=0.892, SNR=8.2dB, signal_weight=0.273, confidence=0.244
INFO:__main__:Candidate 2: R²=0.756, SNR=12.4dB, signal_weight=0.413, confidence=0.312
INFO:__main__:Candidate 3: R²=0.934, SNR=15.1dB, signal_weight=0.503, confidence=0.470
INFO:__main__:Evaluated 47 candidates, found 3 chirps above threshold
Total chirps detected: 3
Average confidence score: 0.751
