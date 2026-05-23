:ClrHome
:Lbl MM
:Menu("GEOMETRY APP","1:COMPUTE AREA/VOL",AV,"2:REVERSE SOLVER",RS,"3:EXIT",EX)
:
:Lbl AV
:Menu("SELECT SHAPE","1:CIRCLE",CI,"2:TRIANGLE",TR,"3:RT TRIANGLE",RT,"4:CUBE",CU,"5:SPHERE",SP,"6:CONE",CO,"7:CYLINDER",CY,"8:NEXT PAGE",NP)
:
:Lbl NP
:Menu("COMPLEX SHAPE","1:FRUSTUM (CONE)",FR,"2:CAP (SPHERE)",SC,"3:MAIN MENU",MM)
:
:Lbl CI
:ClrHome
:Disp "--- CIRCLE ---"
:Input "RADIUS R: ",R
:πR²→A
:2πR→C
:Disp "AREA A:",A
:Disp "CIRCUMF C:",C
:Pause 
:Goto MM
:
:Lbl TR
:ClrHome
:Disp "--- TRIANGLE ---"
:Input "BASE B: ",B
:Input "HEIGHT H: ",H
:0.5BH→A
:Disp "AREA A:",A
:Pause 
:Goto MM
:
:Lbl RT
:ClrHome
:Disp "- RT TRIANGLE -"
:Input "LEG A: ",A
:Input "LEG B: ",B
:0.5AB→X
:√(A²+B²)→C
:Disp "AREA:",X
:Disp "HYPOTENUSE C:",C
:Pause 
:Goto MM
:
:Lbl CU
:ClrHome
:Disp "---- CUBE ----"
:Input "SIDE S: ",S
:S³→V
:6S²→A
:Disp "VOLUME V:",V
:Disp "SURF AREA A:",A
:Pause 
:Goto MM
:
:Lbl SP
:ClrHome
:Disp "--- SPHERE ---"
:Input "RADIUS R: ",R
:(4/3)πR³→V
:4πR²→A
:Disp "VOLUME V:",V
:Disp "SURF AREA A:",A
:Pause 
:Goto MM
:
:Lbl CO
:ClrHome
:Disp "---- CONE ----"
:Input "RADIUS R: ",R
:Input "HEIGHT H: ",H
:(1/3)πR²H→V
:Disp "VOLUME V:",V
:Pause 
:Goto MM
:
:Lbl CY
:ClrHome
:Disp "-- CYLINDER --"
:Input "RADIUS R: ",R
:Input "HEIGHT H: ",H
:πR²H→V
:2πRH+2πR²→A
:Disp "VOLUME V:",V
:Disp "SURF AREA A:",A
:Pause 
:Goto MM
:
:Lbl FR
:ClrHome
:Disp "-CONE FRUSTUM-"
:Input "TOP RAD R1: ",R
:Input "BOT RAD R2: ",M
:Input "HEIGHT H: ",H
:(1/3)πH(R²+R*M+M²)→V
:Disp "VOLUME V:",V
:Pause 
:Goto MM
:
:Lbl SC
:ClrHome
:Disp "- SPHERE CAP -"
:Input "SPH RAD R: ",R
:Input "CAP HGT H: ",H
:(1/3)πH²(3R-H)→V
:Disp "VOLUME V:",V
:Pause 
:Goto MM
:
:Lbl RS
:Menu("REVERSE SOLVER","1:CONE (R FROM V,H)",RC,"2:SPHERE(R FROM V)",RS,"3:CYL (R FROM V,H)",RY,"4:MAIN MENU",MM)
:
:Lbl RC
:ClrHome
:Disp "CONE R SOLVER"
:Input "VOLUME V: ",V
:Input "HEIGHT H: ",H
:√(3V/(πH))→R
:Disp "RADIUS R:",R
:Pause 
:Goto MM
:
:Lbl RS
:ClrHome
:Disp "SPHERE R SOLVER"
:Input "VOLUME V: ",V
:³√(3V/(4π))→R
:Disp "RADIUS R:",R
:Pause 
:Goto MM
:
:Lbl RY
:ClrHome
:Disp "CYL R SOLVER"
:Input "VOLUME V: ",V
:Input "HEIGHT H: ",H
:√(V/(πH))→R
:Disp "RADIUS R:",R
:Pause 
:Goto MM
:
:Lbl EX
:ClrHome
:Disp "APP CLOSED."