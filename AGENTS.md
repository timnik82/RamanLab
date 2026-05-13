# RamanLab Agent Notes

This project is worked on from both WSL on Windows and macOS. Check which environment you are in before choosing launch commands.

Even though the user is technical and tech-savvy, they do not have a developer background, so explain accordingly.

When in doubt about any behavior or architectural decision, ask clarifying questions until there is a complete understanding.

## Launching The 2D Map Analysis GUI

If running from Windows and launching into WSL, use:

```bash
wsl -e bash -c "source ~/coding/RamanLab/ramanlab_env/bin/activate && cd ~/coding/RamanLab && python map_analysis_2d/main.py"
```

If already inside the WSL shell, use the existing `ramanlab_env` virtual environment:

```bash
source ~/coding/RamanLab/ramanlab_env/bin/activate
cd ~/coding/RamanLab
python map_analysis_2d/main.py
```

If on macOS, use the local macOS environment for that checkout instead of the WSL path. For example:

```bash
source ramanlab_env/bin/activate
python map_analysis_2d/main.py
```

On WSL, the window should appear via WSLg. Do not create a new `.venv` for this unless the user explicitly asks for a fresh environment.
