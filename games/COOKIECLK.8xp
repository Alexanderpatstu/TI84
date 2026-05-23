:ClrHome
:0→C
:0→M
:0→L
:0→A
:1→P
:1→G
:Lbl START
:ClrHome
:Disp "===COOKIE CLICKER==="
:Disp ""
:Disp "COOKIES: ",C
:Disp "PER CLICK: ",P
:Disp ""
:Disp "1: CLICK"
:Disp "2: BUY UPGRADE"
:Disp "3: AUTO-CLICKER"
:Disp "4: STATS"
:Disp "5: SAVE"
:Input K
:If K=1
:Goto CLICK
:If K=2
:Goto UPGRADE
:If K=3
:Goto AUTO
:If K=4
:Goto STATS
:If K=5
:Goto SAVE
:Goto START
:Lbl CLICK
:C+P→C
:ClrHome
:Disp "CLICK!"
:Disp "YOU GOT ",P," COOKIES!"
:Disp ""
:Disp "TOTAL: ",C
:Pause
:Goto START
:Lbl UPGRADE
:ClrHome
:Disp "===UPGRADES==="
:Disp ""
:Disp "CURRENT: ",P," PER CLICK"
:Disp ""
:Disp "UPG COST: ",25+25*A
:Disp "COOKIES: ",C
:Disp ""
:Disp "1: BUY 2x"
:Disp "2: BACK"
:Input K
:If K=1
:Goto BUYUPG
:If K=2
:Goto START
:Goto UPGRADE
:Lbl BUYUPG
:If C≥25+25*A
:Then
:C-(25+25*A)→C
:P*2→P
:A+1→A
:ClrHome
:Disp "UPGRADED!"
:Disp "NOW: ",P," PER CLICK"
:Pause
:Else
:ClrHome
:Disp "NOT ENOUGH COOKIES!"
:Pause
:End
:Goto START
:Lbl AUTO
:ClrHome
:Disp "===AUTO-CLICKER==="
:Disp ""
:Disp "COST: 100"
:Disp "RATE: 1 PER SEC"
:Disp ""
:Disp "1: BUY"
:Disp "2: BACK"
:Input K
:If K=1
:Goto BUYAUTO
:If K=2
:Goto START
:Goto AUTO
:Lbl BUYAUTO
:If C≥100
:Then
:C-100→C
:G+1→G
:M+G→M
:ClrHome
:Disp "AUTO-CLICKER"
:Disp "PURCHASED!"
:Disp "RATE: ",G," PER SEC"
:Pause
:Else
:ClrHome
:Disp "NOT ENOUGH COOKIES!"
:Pause
:End
:Goto START
:Lbl STATS
:ClrHome
:Disp "===STATISTICS==="
:Disp ""
:Disp "TOTAL COOKIES: ",C
:Disp "PER CLICK: ",P
:Disp "AUTO-CLICKERS: ",G
:Disp "AUTO EARNED: ",M
:Disp ""
:Disp "PRESS ENTER"
:Input K
:Goto START
:Lbl SAVE
:ClrHome
:Disp "GAME SAVED!"
:Disp ""
:Disp "COOKIES: ",C
:Disp "PER CLICK: ",P
:Disp "AUTO-CLICKERS: ",G
:Pause
:Goto START
