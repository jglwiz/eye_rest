# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **护眼助手** (Eye Rest Assistant) - a Python desktop application that helps users take regular breaks while working on computers to protect their eyes. The application is built using wxPython for the GUI and runs on Windows 10/11.

## Environment Setup

- **Required Environment**: Always use `conda activate eye` before running any tests or executing the application
- **Python Version**: Python 3.x
- **Primary Dependency**: wxPython
- **Platform**: Windows 10/11 with PowerShell

## Development Commands

### Running the Application
```bash
conda activate eye
python src/main.py
```

### Building Executable
```bash
# Build executable (uses PyInstaller)
./build_exe.ps1

# Deploy to specific directories
./deploy.ps1
```

### Dependencies
```bash
pip install wxPython
```

## Code Architecture

### Core Architecture Pattern
The application follows an **event-driven state machine architecture** with clear separation of concerns:

### Key Components

1. **EyeRestCore** (`src/lib/app_core.py`) - Central business logic hub
   - Pure event-driven architecture
   - State machine implementation using `AppState` enum
   - Manages work/rest cycles, timers, and user activity detection
   - Coordinates all other components

2. **State Management** (`src/lib/app_states.py`)
   - `IDLE` - Program started but not working
   - `WORKING` - Active work session timing
   - `RESTING` - Break period active
   - `AWAY` - User away from computer
   - `TEMP_PAUSED` - Temporary pause during rest

3. **UI Components**
   - **MainFrame** (`src/lib/main_window.py`) - Main configuration window
   - **RestScreen** (`src/lib/rest_screen.py`) - Full-screen rest overlay
   - **TaskBarIcon** (`src/lib/taskbar.py`) - System tray integration

4. **Feature Modules**
   - **Config** (`src/lib/config.py`) - Configuration management via `eye_rest_config.json`
   - **HotkeyManager** (`src/lib/hotkey_manager.py`) - Global hotkey handling
   - **ActivityDetector** (`src/lib/activity_detector.py`) - User activity monitoring
   - **StatisticsManager** (`src/lib/statistics_manager.py`) - Usage statistics tracking
   - **RestManager** (`src/lib/rest_manager.py`) - Rest session management

5. **Data Visualization**
   - **StatisticsChart** (`src/lib/statistics_chart.py`) - Daily completion charts
   - **HourlyChart** (`src/lib/hourly_chart.py`) - Hourly usage patterns

### Key Features
- Customizable work/rest intervals
- Global hotkeys for break control
- System tray operation
- Full-screen break reminders
- User activity detection with idle threshold
- Temporary pause functionality during breaks
- Statistics tracking with visual charts
- Sound notifications
- Process duplication prevention

### Configuration System
- Configuration stored in `eye_rest_config.json` in root directory
- Statistics data in `statistics.json`
- Supports idle detection, sound settings, hotkey customization
- Temporary pause feature with configurable duration

### Application Flow
1. **Startup**: Check for existing instance, create lock file
2. **Silent Mode**: If config exists, start working immediately without showing UI
3. **State Transitions**: Work → Rest → Work cycle managed by EyeRestCore
4. **Activity Monitoring**: Continuous user activity detection
5. **Statistics**: Track completed rest sessions and hourly usage patterns

## Testing Guidelines
- Always activate the conda environment before testing
- Test the full work/rest cycle functionality
- Verify hotkey functionality works globally
- Test system tray integration and window management
- Ensure executable builds work correctly

## Code Style Guidelines
- Follow existing modular architecture in `src/lib/` directory
- Use established logging patterns via LoggerManager
- Maintain event-driven architecture principles
- Keep UI logic separate from business logic
- Use the existing configuration and state management patterns

## Important Notes
- The application prevents duplicate instances using lock files
- Configuration determines startup behavior (silent vs. UI mode)
- Full-screen rest overlay is a key security/productivity feature
- Statistics are automatically tracked and persisted
- Temporary pause functionality allows brief interruptions during rest periods