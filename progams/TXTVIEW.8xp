:
:"TEXT VIEWER - TI84 WITH PANIC KEY
:Lbl 0
:ClrHome
:Disp "TEXT VIEWER"
:Disp ""
:Disp "SELECT FILE:"
:Disp ""
:Disp "1. README"
:Disp "2. NOTES"
:Disp "3. INFO"
:Disp "4. EXIT"
:Disp ""
:Disp "CHOOSE:"
:Input CHOICE
:
:If CHOICE = 4
:Then
:ClrHome
:Disp "EXITING..."
:End
:Return
:End
:
:If CHOICE < 1 or CHOICE > 3
:Then
:Goto 0
:End
:
:If CHOICE = 1
:Then
:{"README FILE","LINE 1: WELCOME","LINE 2: THIS IS","LINE 3: A TEXT VIEWER","LINE 4: FOR TI84","LINE 5: PRESS UP/DOWN","LINE 6: TO SCROLL","LINE 7: PRESS 2ND","LINE 8: TO GO BACK"} → L1
:End
:
:If CHOICE = 2
:Then
:{"NOTES FILE","NOTE 1: STUDY","NOTE 2: MATH TESTS","NOTE 3: FORMULA LIST","NOTE 4: IMPORTANT","NOTE 5: KEY DATES","NOTE 6: REVIEW","NOTE 7: TI84 TIPS","NOTE 8: GOOD LUCK"} → L1
:End
:
:If CHOICE = 3
:Then
:{"INFO FILE","VERSION 1.0","TEXT VIEWER","FOR TI84 CE","STORAGE LIMITED","MAX 8 LINES","USE ARROW KEYS","DEL=CLOSE APP"} → L1
:End
:
:0 → PAGE
:1 → VIEWING
:
:While VIEWING = 1
:ClrHome
:Disp "TEXT VIEWER"
:Disp "============"
:Disp ""
:
:For(I,1,min(4,dim(L1)-PAGE*4))
:Disp L1(PAGE*4+I)
:End
:
:Disp ""
:Disp "PG:",PAGE+1,"/ 2"
:Disp "UP=Back DOWN=Next"
:Disp "DEL=CLOSE 2ND=Menu"
:
:getKey → KEY
:
:If KEY = 38
:Then
:If PAGE > 0
:PAGE - 1 → PAGE
:End
:End
:
:If KEY = 40
:Then
:If PAGE < 1
:PAGE + 1 → PAGE
:End
:End
:
:If KEY = 92
:Then
:0 → VIEWING
:End
:
:If KEY = 47
:Then
:0 → VIEWING
:Goto 0
:End
:
:Pause 0.1
:
:End
:
:End