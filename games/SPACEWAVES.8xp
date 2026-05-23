:
:"SPACE WAVES - DIAGONAL FLIGHT GAME
:ClrHome
:Disp "SPACE WAVES"
:Disp ""
:Disp "HOLD KEY TO GO UP"
:Disp "RELEASE TO GO DOWN"
:Disp ""
:Disp "DODGE OBSTACLES"
:Disp "GAIN SCORE"
:Disp ""
:Disp "Press any key..."
:Pause
:
:ClrHome
:"GAME VARIABLES
:0 → SCORE
:64 → POSX
:32 → POSY
:0 → SCROLL
:0 → OBSTCOUNT
:0 → GAMEEND
:1 → DIFFICULTY
:
:"OBSTACLE STORAGE
:{} → OBSTY
:{} → OBSTX
:
:"MAIN GAME LOOP
:While GAMEEND = 0
:
:"CHECK FOR KEY PRESS
:getKey → KEY
:If KEY = 25 or KEY = 34
:Then
:"MOVE UP (y = x diagonal)
:If POSY > 0
:POSY - 2 → POSY
:End
:Else
:"MOVE DOWN (y = -x diagonal)
:If POSY < 62
:POSY + 2 → POSY
:End
:End
:
:"SCROLL OBSTACLES
:SCROLL + 1 → SCROLL
:
:"GENERATE NEW OBSTACLES
:If SCROLL mod (60 - 5*DIFFICULTY) = 0
:Then
:OBSTCOUNT + 1 → OBSTCOUNT
:randInt(0,62) → NEWOBSTY
:augment(OBSTY,NEWOBSTY) → OBSTY
:augment(OBSTX,95) → OBSTX
:End
:
:"UPDATE OBSTACLE POSITIONS
:For(I,1,dim(OBSTX))
:OBSTX(I) - 2 → OBSTX(I)
:If OBSTX(I) < -5
:Then
:SCORE + (10*DIFFICULTY) → SCORE
:"DELETE OBSTACLE
:delvar OBSTY(I)
:delvar OBSTX(I)
:End
:End
:
:"CHECK COLLISIONS
:For(I,1,dim(OBSTX))
:If OBSTX(I) > 60 and OBSTX(I) < 68
:Then
:If abs(POSY - OBSTY(I)) < 8
:Then
:1 → GAMEEND
:End
:End
:End
:
:"INCREASE DIFFICULTY
:If SCORE > 100*DIFFICULTY
:Then
:DIFFICULTY + 1 → DIFFICULTY
:End
:
:"DISPLAY GAME
:ClrHome
:Disp "SCORE: ",SCORE
:Disp "WAVE: ",DIFFICULTY
:Disp ""
:
:"DRAW PLAYER (█)
:Output(8,8,"█")
:
:"DRAW OBSTACLES (■)
:For(I,1,dim(OBSTX))
:If OBSTX(I) > 0 and OBSTX(I) < 95
:Then
:Output(OBSTY(I)/8 + 1, OBSTX(I)/8 + 1,"■")
:End
:End
:
:End
:
:"GAME OVER SCREEN
:ClrHome
:Disp "GAME OVER!"
:Disp ""
:Disp "FINAL SCORE: ",SCORE
:Disp "MAX WAVE: ",DIFFICULTY
:Disp ""
:Disp "Press any key..."
:Pause
:ClrHome
:Disp "Thanks for playing!"
:End