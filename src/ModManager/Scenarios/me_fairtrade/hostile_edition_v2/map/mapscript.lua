--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- DIE SIEDLER: AUFSTIEG EINES KÖNIGREICHS
-- Kampagne / Szenario: Fair Trade (Hostile Edition)
-- Map: me_fairtrade_hostile
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

function Mission_InitPlayers()

    -- 1. Setup Players
    GreenleavesPlayerID = 1 -- Player 1 (Human)
    PlenhamPlayerID     = SetupPlayer(2, "H_NPC_Castellan_ME", "Plenham", "CityColor2")
    WindchillPlayerID   = SetupPlayer(3, "H_NPC_Villager01_ME", "Windchill", "Citycolor3")
    BanditsPlayerID     = SetupPlayer(4, "H_NPC_Mercenary_ME", "Glenwood Bandits", "BanditsColor1")
    CloisterPlayerID    = SetupPlayer(5, "H_NPC_Monk_ME", "Cloister of Metaria", "CloisterColor1")

    -- 2. Start Resources for Player 1 (Greenleaves - Human Player)
    AddResourcesToPlayer(Goods.G_Gold, 300, GreenleavesPlayerID)
    AddResourcesToPlayer(Goods.G_Wood, 150, GreenleavesPlayerID)
    AddResourcesToPlayer(Goods.G_Stone, 50, GreenleavesPlayerID)
    AddResourcesToPlayer(Goods.G_Iron, 20, GreenleavesPlayerID)
    AddResourcesToPlayer(Goods.G_Grain, 20, GreenleavesPlayerID)
    AddResourcesToPlayer(Goods.G_Milk, 20, GreenleavesPlayerID)
    AddResourcesToPlayer(Goods.G_Wool, 20, GreenleavesPlayerID)
 
    -- 3. Start Resources for Player 2 (Plenham - Enemy City)
    AddResourcesToPlayer(Goods.G_Gold, 250, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Wood, 50, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Stone, 30, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Iron, 30, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_RawFish, 30, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Wool, 30, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Milk, 30, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Carcass, 40, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Grain, 30, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Herb, 20, PlenhamPlayerID)
    AddResourcesToPlayer(Goods.G_Honeycomb, 20, PlenhamPlayerID)
  
    -- 4. Start Resources for Player 3 (Windchill - Enemy City)
    AddResourcesToPlayer(Goods.G_Gold, 250, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Wood, 50, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Stone, 30, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Iron, 30, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Carcass, 40, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Wool, 30, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Milk, 30, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Grain, 30, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Herb, 20, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_RawFish, 30, WindchillPlayerID)
    AddResourcesToPlayer(Goods.G_Honeycomb, 20, WindchillPlayerID)

    -- 5. Knight Titles
    SetKnightTitle(GreenleavesPlayerID, KnightTitles.Mayor)
    SetKnightTitle(PlenhamPlayerID, KnightTitles.Earl)
    SetKnightTitle(WindchillPlayerID, KnightTitles.Earl)
		
end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function Mission_SetStartingMonth()

    Logic.SetMonthOffset(3)

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function Mission_InitMerchants()

    -- Trade Offers for Cloister of Metaria
    local CloisterTraderID = Logic.GetStoreHouse(CloisterPlayerID)
    AddOffer(CloisterTraderID, 5, Goods.G_Bread)
    AddOffer(CloisterTraderID, 5, Goods.G_Cheese)
    AddOffer(CloisterTraderID, 5, Goods.G_Medicine)
    AddOffer(CloisterTraderID, 5, Goods.G_Herb)
    AddOffer(CloisterTraderID, 5, Goods.G_Iron)
	
end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function Mission_FirstMapAction()

    -- 1. Initialize Diplomacy & Quests
    Mission_SetDiplomacy()
    Mission_SetupQuests()
	
    -- 2. Initialize AI Profiles
    AIPlayer:new(PlenhamPlayerID, AIProfile_Skirmish, Entities.U_NPC_Castellan_ME)
    AIPlayer:new(WindchillPlayerID, AIProfile_Skirmish, Entities.U_NPC_Castellan_ME)
    AIPlayer:new(CloisterPlayerID, AIPlayerProfile_Village)
    
    -- [NEW] Initiale Verteidigungstruppen für Feindstädte
    local plenhamSpawn = Logic.GetStoreHouse(PlenhamPlayerID)
    if plenhamSpawn ~= 0 then
        local x, y = Logic.GetEntityPosition(plenhamSpawn)
        Logic.CreateBattalionOnUnblockedLand(Entities.U_MilitarySword, x, y, 0, PlenhamPlayerID, 0)
        Logic.CreateBattalionOnUnblockedLand(Entities.U_MilitarySword, x, y, 0, PlenhamPlayerID, 0)
        Logic.CreateBattalionOnUnblockedLand(Entities.U_MilitaryBow, x, y, 0, PlenhamPlayerID, 0)
    end
    
    local windchillSpawn = Logic.GetStoreHouse(WindchillPlayerID)
    if windchillSpawn ~= 0 then
        local x, y = Logic.GetEntityPosition(windchillSpawn)
        Logic.CreateBattalionOnUnblockedLand(Entities.U_MilitarySword, x, y, 0, WindchillPlayerID, 0)
        Logic.CreateBattalionOnUnblockedLand(Entities.U_MilitarySword, x, y, 0, WindchillPlayerID, 0)
        Logic.CreateBattalionOnUnblockedLand(Entities.U_MilitaryBow, x, y, 0, WindchillPlayerID, 0)
    end
	
    -- 3. Start Continuous Background Jobs
    StartSimpleJob("CheckMonth")
    StartSimpleJob("CheckResourcesforAI")
    StartSimpleJob("AttackCountdown")
    StartSimpleJob("CarePackageJob")
	
end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function Mission_SetDiplomacy()

    -- Player 1 is at war with the rival cities Plenham and Windchill
    SetDiplomacyState(GreenleavesPlayerID, PlenhamPlayerID, DiplomacyStates.Enemy)
    SetDiplomacyState(GreenleavesPlayerID, WindchillPlayerID, DiplomacyStates.Enemy)
		
    -- Plenham and Windchill are allied against Player 1
    SetDiplomacyState(PlenhamPlayerID, WindchillPlayerID, DiplomacyStates.Allied)

    -- Cloister starts Undecided with Player 1, but has trade contacts with the other cities
    SetDiplomacyState(GreenleavesPlayerID, CloisterPlayerID, DiplomacyStates.Undecided)
    SetDiplomacyState(PlenhamPlayerID, CloisterPlayerID, DiplomacyStates.TradeContact)
    SetDiplomacyState(WindchillPlayerID, CloisterPlayerID, DiplomacyStates.TradeContact)
    SetDiplomacyState(BanditsPlayerID, CloisterPlayerID, DiplomacyStates.TradeContact)

    -- Bandits initial relations
    SetDiplomacyState(GreenleavesPlayerID, BanditsPlayerID, DiplomacyStates.Undecided)
    SetDiplomacyState(PlenhamPlayerID, BanditsPlayerID, DiplomacyStates.Undecided)
    SetDiplomacyState(WindchillPlayerID, BanditsPlayerID, DiplomacyStates.Undecided)
	
end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function Mission_SetupQuests()

    -- Bandits discovery feedback trigger
    QuestTemplate:New("", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.Discover, 2, { BanditsPlayerID } } },
        { { Triggers.Time, 0 } },
        0,
        nil,
        nil,
        FirstFeedback, nil, false, false)

    -- Bandits defeat trigger
    QuestTemplate:New("", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.DestroyPlayers, BanditsPlayerID } },
        { { Triggers.Time, 0 } },
        0,
        nil,
        nil,
        function() BanditsDefeated = true end, nil, false, false)

    --------------------------------------------------------------------------------------------------
    -- PFAD 1: FREIHANDEL & KLOSTER-METARIA LIEFERKETTE (Wirtschaftssieg)
    --------------------------------------------------------------------------------------------------
    local FindMetariaQuestID = QuestTemplate:New("Quest_Discover_Cloister", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.Discover, 2, { CloisterPlayerID } } },
        { { Triggers.Time, 0 } },
        0,
        nil,
        nil,
        CloisterUndecided, nil, true, true)
				
    local DeliverClothesQuestID = QuestTemplate:New("Quest_Deliver_GC_Clothes", CloisterPlayerID, GreenleavesPlayerID,
        { { Objective.Deliver, Goods.G_Clothes, 5 } },
        { { Triggers.Quest, FindMetariaQuestID, QuestResult.Success } },
        0,
        { { Reward.Diplomacy, CloisterPlayerID, 1 } },
        nil,
        CloisterEstablishedContact, nil, true, true)
			
    local DeliverHygieneQuestID = QuestTemplate:New("Quest_Deliver_GC_Hygiene", CloisterPlayerID, GreenleavesPlayerID,
        { { Objective.Deliver, Goods.G_Broom, 10 } },
        { { Triggers.Quest, DeliverClothesQuestID, QuestResult.Success } },
        0,
        { { Reward.Diplomacy, CloisterPlayerID, 1 } },
        nil,
        CloisterTradeContact, nil, true, true)

    local DeliverBeerQuestID = QuestTemplate:New("Quest_Deliver_GC_Entertainment", CloisterPlayerID, GreenleavesPlayerID,
        { { Objective.Deliver, Goods.G_Beer, 15 } },
        { { Triggers.Quest, DeliverHygieneQuestID, QuestResult.Success } },
        0,
        { { Reward.Diplomacy, CloisterPlayerID, 1 } },
        nil,
        CloisterAllied, nil, true, true)
						
    local DeliverGoldQuestID = QuestTemplate:New("Quest_Deliver_GC_Gold", CloisterPlayerID, GreenleavesPlayerID,
        { { Objective.Deliver, Goods.G_Gold, 5000 } },
        { { Triggers.Quest, DeliverBeerQuestID, QuestResult.Success } },
        0,
        nil,
        nil,
        CheckVictoryCondition, nil, true, true)

    --------------------------------------------------------------------------------------------------
    -- PFAD 2: MILITÄRISCHE UNTERWERFUNG DER FEINDSTÄDTE (Militärsieg)
    --------------------------------------------------------------------------------------------------
    local DestroyPlenhamQuestID = QuestTemplate:New("", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.DestroyPlayers, PlenhamPlayerID } },
        { { Triggers.Time, 0 } },
        0,
        nil,
        nil, nil, nil, false, false)

    local DestroyWindchillQuestID = QuestTemplate:New("", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.DestroyPlayers, WindchillPlayerID } },
        { { Triggers.Time, 0 } },
        0,
        nil,
        nil, nil, nil, false, false)

    local MilitaryFightQuestID = QuestTemplate:New("Quest_DestroyPlayers_City", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.Quest, { DestroyPlenhamQuestID, DestroyWindchillQuestID } } },
        { { Triggers.Time, 0 } },
        0,
        nil,
        nil,
        CheckVictoryCondition, nil, false, true)

    --------------------------------------------------------------------------------------------------
    -- GESAMT-SIEGBEDINGUNG (Handelssieg ODER Militärsieg)
    --------------------------------------------------------------------------------------------------
    WinConditionID, WinCondition = QuestTemplate:New("", GreenleavesPlayerID, GreenleavesPlayerID,
        { { Objective.Quest, { DeliverGoldQuestID, MilitaryFightQuestID } } },
        { { Triggers.Time, 0 } },
        0,
        { { Reward.Victory } },
        nil, nil, nil, false, false)

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Siegprüfung: Sobald entweder der Handelsabschluss oder der Militärsieg erreicht ist
function CheckVictoryCondition(_Quest)

    if _Quest.State == QuestState.Over and _Quest.Result == QuestResult.Success then
        WinCondition:Success()
    end

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- RESSOURCEN-LIEFERUNG (Verhindert Lagerhaus-Überfüllung)
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
CarePackageIronDelivered = 0
function CarePackageJob()
    if CarePackageIronDelivered < 1200 then
        if CarePackageCounter == nil or CarePackageCounter <= 0 then
            CarePackageCounter = 600 -- 10 Minuten Intervall
        end
        
        CarePackageCounter = CarePackageCounter - 1
        
        if CarePackageCounter <= 0 then
            -- Lieferung alle 10 Minuten
            AddResourcesToPlayer(Goods.G_Iron, 30, GreenleavesPlayerID)
            AddResourcesToPlayer(Goods.G_Stone, 20, GreenleavesPlayerID)
            CarePackageIronDelivered = CarePackageIronDelivered + 30
        end
    else
        return true -- Job beenden
    end
end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 45-MINUTEN SCHONFRIST-TIMER (2700 Sekunden)
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function AttackCountdown()

    if AttackWaitCounter == nil then
        AttackWaitCounter = 2700 -- 45 Minuten Schonfrist in Sekunden
    end

    AttackWaitCounter = AttackWaitCounter - 1

    -- Wenn 30 Minuten abgelaufen sind, starten die Angriffe
    if AttackWaitCounter <= 0 then
        -- Akustische Warnung an den Spieler
        SendVoiceMessage(PlenhamPlayerID, "DiplomacyChanged_Enemy")

        -- Erster Angriffsschlag
        LaunchFirstAttack()

        -- Starte die zyklischen Angriffswellen
        StartSimpleJob("AttackWavesJob")
        return true
    end

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Erster koordinierter Angriff nach 30 Minuten
function LaunchFirstAttack()

    local playerStorehouse = Logic.GetStoreHouse(GreenleavesPlayerID)

    -- Angriff Plenham: 1 Schwert, 1 Bogen
    local plenhamSpawn = Logic.GetStoreHouse(PlenhamPlayerID)
    if plenhamSpawn ~= 0 and playerStorehouse ~= 0 then
        AIScript_SpawnAndAttackCity(PlenhamPlayerID, playerStorehouse, plenhamSpawn, 1, 1, 0, 0, 0, 0)
    end

    -- Angriff Windchill: 1 Schwert, 1 Bogen
    local windchillSpawn = Logic.GetStoreHouse(WindchillPlayerID)
    if windchillSpawn ~= 0 and playerStorehouse ~= 0 then
        AIScript_SpawnAndAttackCity(WindchillPlayerID, playerStorehouse, windchillSpawn, 1, 1, 0, 0, 0, 0)
    end

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- Zyklische & eskalierende Angriffswellen (alle 10 Minuten / 600s nach Minute 30)
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function AttackWavesJob()

    if WaveIntervalCounter == nil or WaveIntervalCounter <= 0 then
        WaveIntervalCounter = 600 -- 10 Minuten Intervall zwischen den Wellen
    end

    WaveIntervalCounter = WaveIntervalCounter - 1

    if WaveIntervalCounter <= 0 then

        local playerStorehouse = Logic.GetStoreHouse(GreenleavesPlayerID)
        local plenhamSpawn = Logic.GetStoreHouse(PlenhamPlayerID)
        local windchillSpawn = Logic.GetStoreHouse(WindchillPlayerID)

        if playerStorehouse == 0 then
            return false
        end

        if CurrentWaveIndex == nil then
            CurrentWaveIndex = 1
        else
            CurrentWaveIndex = CurrentWaveIndex + 1
        end

        -- Welle 1 (Minute 40): 2 Schwert, 1 Bogen
        if CurrentWaveIndex == 1 then
            if plenhamSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(PlenhamPlayerID, playerStorehouse, plenhamSpawn, 2, 1, 0, 0, 0, 0)
            end
            if windchillSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(WindchillPlayerID, playerStorehouse, windchillSpawn, 1, 2, 0, 0, 0, 0)
            end

        -- Welle 2 (Minute 50): 2 Schwert, 2 Bogen + 1 Rammbock
        elseif CurrentWaveIndex == 2 then
            if plenhamSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(PlenhamPlayerID, playerStorehouse, plenhamSpawn, 2, 2, 0, 0, 1, 0)
            end
            if windchillSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(WindchillPlayerID, playerStorehouse, windchillSpawn, 2, 2, 0, 0, 0, 0)
            end

        -- Welle 3 (Minute 60): 3 Schwert, 2 Bogen + 1 Katapult + 1 Ramme
        elseif CurrentWaveIndex == 3 then
            if plenhamSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(PlenhamPlayerID, playerStorehouse, plenhamSpawn, 3, 2, 1, 0, 1, 0)
            end
            if windchillSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(WindchillPlayerID, playerStorehouse, windchillSpawn, 2, 2, 0, 1, 1, 0)
            end

        -- Welle 4+ (Minute 70 und fortlaufend): Volle Belagerungsstreitmacht
        else
            if plenhamSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(PlenhamPlayerID, playerStorehouse, plenhamSpawn, 3, 3, 1, 1, 1, 1)
            end
            if windchillSpawn ~= 0 then
                AIScript_SpawnAndAttackCity(WindchillPlayerID, playerStorehouse, windchillSpawn, 3, 3, 1, 1, 1, 0)
            end
        end

    end

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- KI-LAGERHAUS-REGULATOR (Verhindert Blockaden & sichert KI-Produktion)
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function CheckResourcesforAI()

    -- PLENHAM (Player 2)
    -- Überschüsse abbauen
    if GetPlayerResources(Goods.G_Stone, PlenhamPlayerID) >= 80 then
        RemoveResourcesFromPlayer(Goods.G_Stone, 40, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Wood, PlenhamPlayerID) >= 100 then
        RemoveResourcesFromPlayer(Goods.G_Wood, 40, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Iron, PlenhamPlayerID) >= 60 then
        RemoveResourcesFromPlayer(Goods.G_Iron, 30, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Wool, PlenhamPlayerID) >= 80 then
        RemoveResourcesFromPlayer(Goods.G_Wool, 40, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Grain, PlenhamPlayerID) >= 80 then
        RemoveResourcesFromPlayer(Goods.G_Grain, 40, PlenhamPlayerID)
    end
    -- Grundnahrung nachfüllen
    if GetPlayerResources(Goods.G_RawFish, PlenhamPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_RawFish, 25, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Carcass, PlenhamPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_Carcass, 25, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Milk, PlenhamPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_Milk, 25, PlenhamPlayerID)
    end
    if GetPlayerResources(Goods.G_Grain, PlenhamPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_Grain, 25, PlenhamPlayerID)
    end

    -- WINDCHILL (Player 3)
    -- Überschüsse abbauen
    if GetPlayerResources(Goods.G_Stone, WindchillPlayerID) >= 80 then
        RemoveResourcesFromPlayer(Goods.G_Stone, 40, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Wood, WindchillPlayerID) >= 100 then
        RemoveResourcesFromPlayer(Goods.G_Wood, 40, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Iron, WindchillPlayerID) >= 60 then
        RemoveResourcesFromPlayer(Goods.G_Iron, 30, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Wool, WindchillPlayerID) >= 80 then
        RemoveResourcesFromPlayer(Goods.G_Wool, 40, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Grain, WindchillPlayerID) >= 80 then
        RemoveResourcesFromPlayer(Goods.G_Grain, 40, WindchillPlayerID)
    end
    -- Grundnahrung nachfüllen
    if GetPlayerResources(Goods.G_RawFish, WindchillPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_RawFish, 25, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Carcass, WindchillPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_Carcass, 25, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Milk, WindchillPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_Milk, 25, WindchillPlayerID)
    end
    if GetPlayerResources(Goods.G_Grain, WindchillPlayerID) <= 1 then
        AddResourcesToPlayer(Goods.G_Grain, 25, WindchillPlayerID)
    end

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- MONATLICHE BANDITEN-DYNAMIK
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function CheckMonth()

    ThisMonthCheck = Logic.GetCurrentMonth()
	
    if ThisMonthCheck ~= LastMonthCheck then
        -- Banditen verhalten sich erst nach Ablauf der Schonfrist dynamisch
        if not BanditsDefeated then
            if AttackWaitCounter == nil or AttackWaitCounter <= 0 then
                SetBanditsDiplomacy()
            end
        end
    end
	
    LastMonthCheck = ThisMonthCheck

end

function SetBanditsDiplomacy()
	
    local dummy = Logic.GetRandom(3)
    if dummy == 0 then
        SetDiplomacyState(GreenleavesPlayerID, BanditsPlayerID, DiplomacyStates.Enemy)
    elseif dummy == 1 then
        SetDiplomacyState(GreenleavesPlayerID, BanditsPlayerID, DiplomacyStates.Undecided)
    elseif dummy == 2 then
        SetDiplomacyState(GreenleavesPlayerID, BanditsPlayerID, DiplomacyStates.EstablishedContact)
    end
    SendFeedback()

end

function FirstFeedback()

    state = Diplomacy_GetRelationBetween(GreenleavesPlayerID, BanditsPlayerID)
	
    if state == -2 then
        SendVoiceMessage(BanditsPlayerID, "DiplomacyChanged_Enemy")
    elseif state == -1 then
        SendVoiceMessage(BanditsPlayerID, "DiplomacyChanged_Undecided")
    elseif state == 0 then
        SendVoiceMessage(BanditsPlayerID, "DiplomacyChanged_Established")
    end
		
    FeedbackActive = true
	
end

function SendFeedback()

    state = Diplomacy_GetRelationBetween(GreenleavesPlayerID, BanditsPlayerID)
	
    if state ~= oldState and FeedbackActive ~= nil then
        if state == -2 then
            SendVoiceMessage(BanditsPlayerID, "DiplomacyChanged_Enemy")
        elseif state == -1 then
            SendVoiceMessage(BanditsPlayerID, "DiplomacyChanged_Undecided")
        elseif state == 0 then
            SendVoiceMessage(BanditsPlayerID, "DiplomacyChanged_Established")
        end
    end
	
    oldState = state

end

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- SPRACHNACHRICHTEN FÜR KLOSTER-FORTSCHRITT
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
function CloisterUndecided()

    SendVoiceMessage(CloisterPlayerID, "DiplomacyChanged_Undecided")

end

function CloisterEstablishedContact()

    SendVoiceMessage(CloisterPlayerID, "DiplomacyChanged_Established")
	
end

function CloisterTradeContact()
	
    SendVoiceMessage(CloisterPlayerID, "DiplomacyChanged_TradeContact")
	
end

function CloisterAllied()

    SendVoiceMessage(CloisterPlayerID, "DiplomacyChanged_Allied")

end
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
