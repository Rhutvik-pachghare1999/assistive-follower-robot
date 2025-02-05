# Dataset Preparation for Shoe Detection

## Data Collection

### Hardware Setup
- TurtleBot 4 + OAK-D Camera
- Raspberry Pi 4 (running DepthAI)
- Custom data collection script

### Collection Process
1. Place user at various distances (0.5m - 3.0m)
2. Various angles (-45° to +45°)
3. Different lighting conditions
4. Multiple users, different shoe types

### Annotation Format (CSV)
```csv
filename,x_offset_norm,z_distance_norm,sin_theta,cos_theta
frame_001.jpg,0.12,0.45,0.15,0.99
frame_002.jpg,-0.08,0.32,-0.22,0.98
```

### Normalization
- `x_offset_norm`: [-1, 1] (left to right across image)
- `z_distance_norm`: [0, 1] (0 = 0mm, 1 = 2000mm)
- `sin_theta`, `cos_theta`: [-1, 1] for angle continuity

## Dataset Structure
```
data/
├── annotations.csv
└── images/
    ├── frame_001.jpg
    ├── frame_002.jpg
    └── ...
```

## Split
- Train: 80%
- Validation: 10%
- Test: 10%

Stratified by angle bins to ensure balanced distribution.
