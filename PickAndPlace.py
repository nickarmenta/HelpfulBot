def Setup():
  # Setup sequence and prompts
  global partMass=request_float_from_primary_client("How much does your part weigh in kilos? (2.2lbs/kg)")
  # Get part length (mm)
  global CoG_Z=request_float_from_primary_client("How tall is the part in millimeters? (25.4mm/in)")
  # Create new center of gravity based on part length
  global CoG_Z=CoG_Z/2000+.05
  # Get part diameter (mm)
  global palletGap=request_float_from_primary_client("How wide is the part in millimeters? (24.5mm/in)")
  global palletGap=palletGap/500
  # Get rows in pallet
  global palletRows=request_integer_from_primary_client("How many rows do you want to make?")
  # Get columns in pallet
  global palletColss=request_integer_from_primary_client("How many columns do you want to make?")
  # Initialize rows and columns
  global activeRow=0
  global activeCol=0
  # Get gripper open/close output
  global gripperOutput=request_integer_from_primary_client("Which output is my gripper wired to?")
  # Get machine cycle output
  global cycleOutput=request_integer_from_primary_client("Which output is your machine wired to?")
  # Get part sensor input
  global partInput=request_integer_from_primary_client("Which input tells me the part is there?")
  # Get cycle finished input
  global cycleInput=request_integer_from_primary_client("Which input tells me the machine is done?")
end

def AlignRobot(rawPose):
  set_tcp(p[0.0,0.0,0.0,0.0,0.0,0.0])
  set_payload(0.0,[0.0,0.0,0.0])
  set_gravity([0.0, 0.0, 9.82])
  local newPose=rawPose
  newPose[5]=0.0
  return newPose
end

def TeachPick():
  # Create pick, approach, and depart positions
  local pickTest=False  
  while (pickTest==False):
    # Open gripper and get pick position
    popup("Hold this part, I'm about to drop it!", "Message", False, False, blocking=True)
    set_digital_out(gripperOutput, False)
    freedrive_mode()
    popup("Move me to where you want to grab the part!", "Message", False, False, blocking=True)
    end_freedrive_mode()
    global pickPose=AlignRobot(get_actual_tcp_pose())
    movel(pickPose, a=0.125, v=0.2)
    freedrive_mode()
    set_digital_out(gripperOutput, True)
    sleep(0.5)
    end_freedrive_mode()
    
    # Create positions and test
    global approachPick=pose_trans(pickPose, p[0,0,CoG_Z*2,0,0,0])
    global departPick=pose_trans(pickPose, p[0,0,CoG_Z,0,0,0])
    popup("Alright let me try!", "Message", False, False, blocking=True)
    set_digital_out(gripperOutput, False)
    sleep(0.5)
    movel(approachPick, a=0.125, v=0.2)
    movel(pickPose, a=0.125, v=0.2)
    set_digital_out(gripperOutput, True)
    sleep(0.5)
    movel(departPick, a=0.125, v=0.2)

    # Confirm position correct
    pickTest=request_boolean_from_primary_client("Did I pick it okay??")
  end
  return
end

def TeachRelay():
  # Move to relay position
  freedrive_mode()
  popup("Move me to a safe spot between the pick and place points", "Message", False, False, blocking=True)
  end_freedrive_mode()
  global relayPose=get_actual_tcp_pose()
  return
end

def TeachPlace():
  local placeTest=False
  while (placeTest==False):
    # Move to place position
    freedrive_mode()
    popup("Move me to where you want to put your part!", "Message", False, False, blocking=True)
    end_freedrive_mode()
    global placePose=AlignPose(get_actual_tcp_pose())
    set_digital_out(gripperOutput, False)
    sleep(0.5)
    
    # Create positions and test
    global approachPlace=pose_trans(placePose, p[0,0,CoG_Z*2,0,0,0])
    global departPlace=pose_trans(placePose, p[0,0,Cog_Z,0,0,0])
    popup("Alright let me try!", "Message", False, False, blocking=True)
    set_digital_out(gripperOutput, True)
    sleep(0.5)
    movel(approachPlace, a=0.125, v=0.2)
    movel(placePose, a=0.125, v=0.2)
    set_digital_out(gripperOutput, True)
    sleep(0.5)
    movel(departPlace, a=0.125, v=0.2)

    # Confirm position correct
    placeTest=request_boolean_from_primary_client("Did I place the part okay?")
  end
  return
end

def TeachPallet():
  local palletTest=False
  while (palletTest==False):
    freedrive_mode()
    popup("Move me just above where you want to start putting your finished parts", "Message", False, False, blocking=True)
    end_freedrive_mode()
    local seekPose=AlignPose(pose_add(p[0,0,-.075,0,0,0], get_actual_tcp_pose()))
    # Do downward force move to surface
    zero_ftsensor()
    force_mode(p[0.0,0.0,0.0,0.0,0.0,0.0], [0, 0, 1, 1, 1, 0], [0.0, 0.0, -5.0, 0.05, 0.05, 0.1], 3, [0.1, 0.1, 0.15, 0.05, 0.05, 0.3])
    movel(seekPose, a=0.05, v=0.05)
    end_force_mode()
    stopl(5.0)
    # Create first pallet position just above surface
    global palletPose=AlignPose(pose_add(p[0,0,0.003,0,0,0], get_actual_tcp_pose()))
    global approachPallet=pose_add(p[0,0,CoG_Z*1.3,0,0,0], palletPose)
    global departPallet=pose_trans(palletPose, p[0,0,-CoG_Z,0,0,0])
    # Test pallet routine
    popup("Alright let me try!", "Message", False, False, blocking=True)
    movel(approachPallet, a=0.125, v=0.2)
    movel(palletPose, a=0.125, v=0.2)
    set_digital_out(gripperOutput, False)
    movel(departPallet, a=0.125, v=0.2)
    palletTest=request_boolean_from_primary_client("Did I place the part okay?")
end

def CreatePalletPose():
  global palletOffset=p[activeRow*palletGap,activeCol*palletGap,0,0,0,0]
  global cur_approach= pose_add(approachPallet, palletOffset)
  global cur_position= pose_add(palletPose, palletOffset)
  global cur_depart= pose_add(departPallet, palletOffset)
  global activeCol=activeCol+1
  global activeRow=activeRow+1
  if (activeRow>palletRows):
    global activeRow=0
  end
  if (activeCol>palletCols):
    global activeCol=0
  end
  return
end
  
def PnPWizard():
  Setup()
  TeachPick()
  TeachRelay()
  TeachPlace()
  TeachPallet()
  popup("I think I got it! Ready to try it out!", "Message", False, False, blocking=True)

def PickCycle():
  # Go to pick part
  movej(approachPick, a=3, v=1.5)
  movel(pickPose, a=0.25, v=0.25)
  set_digital_out(gripperOutput, True)
  sleep(0.5)
  movel(departPose, a=0.25, v=0.25)
  return
end

def PlaceCycle():
  movej(approachPlace, a=3, v=1.5, r=0.2)
  movel(placePose, a=0.25, v=0.25)
  set_digital_out(gripperOutput, False)
  sleep(0.5)
  movel(departPlace, a=0.25, v=0.25)
  return
end

def RunProgram():
  while (True):
    # If part is ready
    if (partInput==True):
      PickCycle()
      movej(relayPose, a=3, v=1.5, r=0.2)
      PlaceCycle()
      movej(relayPose, a=3, v=1.5, r=0.2)

      # Pulse cycle output
      set_digital_out(cycleOutput, True)
      sleep(0.5)
      set_digital_out(cycleOutput, Falsee)

      while (cycleInput==False):
        end

      # Pick part
      movej(approachPlace, a=3, v=1.5, r=0.2)
      movel(placePose, a=0.25, v=0.25)
      set_digital_out(gripperOutput, True)
      sleep(0.5)
      movel(departPlace, a=0.25, v=0.25)

      # Palletize routine
      CreatePalletPose()
      movej(relayPose, a=3, v=1.5, r=0.2)
      movej(cur_approach, a=3, v=1.5)
      movel(cur_position, a=0.25, v=0.25)
      set_digital_out(gripperOutput, False)
      sleep(0.5)
      movel(cur_depart, a=0.25, v=0.25)
    end
  end
end
