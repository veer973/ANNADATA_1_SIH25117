# ANNADATA_1_SIH25117
TEAM NAME : ANNADATA_01
🛰️ Annadata_1 – Autonomous Field Rover (ESP32 + GPS + ESP-Now)
Annadata_1 is an autonomous agricultural rover designed to travel through farm fields in a serpentine (zig-zag) pattern using parameters such as field length, field width, and row spacing.
The system uses a Master–Slave ESP32 architecture, where the master sends field parameters wirelessly via ESP-Now, and the rover executes fully automated movement.
🚜 Key Features
ESP32 Master–Slave communication using ESP-Now
Master ESP sends field dimensions and start command wirelessly to the rover.
Autonomous navigation logic
Rover calculates travel distance using the formula:
speed = distance / time
Then moves forward → turns ~90° → travels row spacing → turns back → repeats.
(Perfect precision not required; practical automation first.)
GPS-based monitoring (Neo-M8N)
Rover reads live GPS data to monitor position and check for movement status (lock/no-lock).
Cytron Motor Driver integration
Smooth DC motor control for forward, reverse, and turning operations.
Failsafe & Debug logs
Serial output reports GPS lock status, ESP-Now packet status, and rover actions.
🧩 Tech Stack
Hardware: ESP32, Neo-M8N GPS, Cytron MD motor driver, DC motors
Protocols: ESP-Now, UART, GPS NMEA
Software: Arduino framework (C/C++), TinyGPS++, ESP-Now API
📌 Current Capabilities
Accepts field inputs:
Field Length
Field Width
Row Spacing
Starts autonomous mode when Master sends startAuto = true.
Executes a multi-row serpentine path automatically.
Prints GPS status (locked / not locked) for debugging.
🚧 Next Improvements
IMU-based angle correction
PID tuning for straighter paths
Accurate 90° turns
Real-time map logging
Obstacle avoidance modul
FILES ASSOCIATED TO THE PROJECT:
1. SOLAR SUNFLOWER.odt -> CONSISTS THE CODE FOR THE SOLAR SUNFLOWER PATTERN IN WHICH THE SOLAR PANEL FOLLOWS THE DIRECTION OF SUN WHERE THERE IS MAXIMUM INTENSITY
2. AUTOMATED SOIL ANALYSIS REPORT.odt -> CONSISTS THE CODE FOR THE FUNCTIONS USED IN THE WEBSITE FOR SOIL TEST ANALYSIS
3. CODE FOR CO-ORDINATE CALCULATION USING GPS.odt -> CONSISTS THE CODE FOR CO-ORDINATE CALCULUS USING GPS MODULE FOR DISTANCE WAY-POINT NAVIGATION AND SELECTIVE SPRINKLING
4. MASTER CODE FOR ROVER  COMMUNICATION.odt -> CONSISTS THE CODE FOR COMMUNICATION BETWEEN THE ROVER IN THE FIELD WITH BASE STATION FROM MASTER ESP's END
5. SLAVE CODE FOR ROVER COMMUNICATION.odt -> CONSISTS THE CODE FOR COMMUNICATION BETWEEN THE ROVER IN THE FIELD WITH BASE STATION FROM SLAVE'S END, i.e., ROVER's END\
6. SEED DISPERSAL.odt -> CONSISTS THE EMBEDDED SYSTEM CODE FOR SEED SOWING
7. ROSS CODE FOR AUTOMATED DRONE SIMULATION.odt -> CONSISTS THE CODE FOR DRONE AUTOMATION SIMULATION
8. ROSS CODES FOR ROVER AUTOMATED ROVER SIMULATION.odt -> CONSISTS THE CODE FOR ROVER AUTOMATION SIMULATION
