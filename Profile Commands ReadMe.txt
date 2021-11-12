G0 Set Command Interval
G1 Digital Output Control
G2 Lamp Control
G3 Temperature Control
G4 Recorder Control
G5 Profile Execution Control
G6 Data Collection and Refresh Control
G7 Pump Control
G8 Temperature Sensor Setup

G0 commands: I
	I[float] : sets wait time between lines in seconds

G1 commands: T, A, X
	T[0-20] : selects channel for "A" command. 
	A[0-1] : Sets selected channel on (1) or off (0)
	X : Sends output of all 20 channels

G2 commands: X
	X[0-1] : turns the lamp on (1) or off (0)

G3 commands: X, T, A, H, R, U, L
	X[0-1] : turns temperature control on (1) or off (0)
	T[0-5] : selects temperature sensor channel for "A" command
	A[0-1] : sets selected channel on (1) or off (0) for use with temperature control
	H[0-1] : sets temperature mode to Heat (1) or Cool (0)
	R[0-1] : sets temperature sensor reduction mode to Median (1) or Mean (0) 
	U[float] : sets the temperature upper limit in deg C
	L[float] : sets the temperature lower limit in deg C

G4 commands: X, S
	X : Activates or deactivates recording (toggles)
	S;[string] :sets file and path for where to record data. Must include semicolon as indicated. 

G5 commands: X, S, L
	X[0-4] : activates or deactivates selected profile (toggles). X0 is "Execute Profile", and X[1-4] is for "Custom 1-4"
	S[0-4];[string] : assigns a file to the selected profile. profile 0 is the "Execute Profile". Semicolon is critical. Do not put spaces in this command. 
	L[int] : Go to Line in currently running file. "L0" will restart the profile.

G6 commands: T, A, X
	T[0-24] : selects channel for "A" command
	A[0-1] : sets selected channel to be updated (1) or not-updated (0)
	X : Updates all selected channels

G7 commands: X
	x[0-1] : turns the pump on (1) or off (0)

G8 commands: S
	S[1-5];[string] : assignes a temp sensor to the selected temp channel. Semicolon is critical. Do not put spaces in this command.




