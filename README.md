# Automotive Dashboard Simulator (AUTOSIM)

## 1. What is this project?

Automotive Dashboard Simulator is a Linux-based automotive cockpit simulation developed using Python, PySide6 and CAN bus communication.

It demonstrates how different Electronic Control Units (ECUs) inside a vehicle communicate through the Controller Area Network (CAN) protocol.

The project simulates:

- Engine start and stop
- Vehicle speed and RPM
- Gear shifting
- Acceleration and braking
- Steering controls
- Fuel and battery monitoring
- Tyre pressure and temperature
- Vehicle lighting and indicators

It displays vehicle information through an interactive automotive dashboard with seven screens, live gauges and a CAN monitoring system.

**Purpose:** To demonstrate automotive embedded software concepts, ECU communication, CAN bus technology and vehicle dashboard simulation.

## 2. How to download and install

### Step 1: Download the project

Open the GitHub repository:

https://github.com/Mukilan7978/Dashboard_car_can-

Click the green **Code** button and select **Download ZIP**.

Alternatively, use the Linux terminal:

```bash
git clone https://github.com/Mukilan7978/Dashboard_car_can-.git
```

### Step 2: Open the project

```bash
cd Dashboard_car_can-
```

### Step 3: Install system dependencies

For Ubuntu/Debian Linux:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip can-utils iproute2
```

### Step 4: Create a Python virtual environment

```bash
python3 -m venv .venv
```

### Step 5: Install project dependencies

```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Configure the virtual CAN interface

```bash
sudo modprobe vcan
./tools/setup_vcan.sh
```

### Step 7: Run the simulator

```bash
./run.sh
```

The simulator starts with its dashboard and supporting CAN monitoring processes.

## 3. How does the project work?

The project operates through communication between a vehicle simulator, multiple ECUs, a CAN bus and a graphical dashboard.

### 1. Vehicle Simulation

The vehicle simulator generates information such as vehicle speed, engine RPM, temperature, fuel level, gear position and steering inputs.

### 2. Electronic Control Units (ECUs)

Different ECUs handle specific vehicle functions:

- **Engine ECU:** Engine information and performance.
- **Transmission ECU:** Gear and clutch information.
- **Body ECU:** Lighting, indicators and vehicle body information.

### 3. Gateway ECU

The Gateway ECU validates CAN messages, checks message ownership and signal values, and controls their transmission.

### 4. CAN Bus Communication

Validated vehicle information is transmitted as CAN frames through the Linux virtual CAN interface (`vcan0`).

### 5. Dashboard Display

The dashboard receives and decodes CAN frames and displays vehicle information through gauges, indicators and dashboard screens.

### System Workflow

**Vehicle Simulator → ECUs → Gateway ECU → CAN Bus (`vcan0`) → CAN Decoder → Automotive Dashboard**

The simulator and dashboard operate as separate processes. Vehicle information travels through CAN communication rather than direct access to the simulator's internal vehicle state.

---

**Note:** This is an educational software simulator. It does not connect to or control a real vehicle. The CAN identifiers are project-defined and are not confirmed BMW vehicle specifications.
