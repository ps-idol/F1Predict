GRID_ADJUSTMENT_COEFFICIENT = 40
GA_ELO_INTERCEPT_COEFFICIENT = 0
K_FACTOR = 8
RETIREMENT_PENALTY = -0.8
FINISHING_BONUS = 0.1
BASE_RETIREMENT_PROBABILITY = 0.05
RETIREMENT_PROBABILITY_CHANGE_WEIGHT = 0.05
ROOKIE_DRIVER_RATING = 1800


DRIVER_WEIGHTING = 0.2
CONSTRUCTOR_WEIGHTING = 0.7
ENGINE_WEIGHTING = 0.1

from python.f1Models import Engine, Constructor
from random import randint

class EloDriver:
    def __init__(self, name, constructor):
        self.name = name
        self.trackRatings = {}
        self.constructor = constructor
        self.rating = 2200  # Default rating
    def changeConstructor(self, constructor): # Spelling mistake
        self.constructor = constructor

class EloRaceModel:
    def __init__(self, drivers, constructors, engines, tracks):
        self.drivers = drivers
        # TODO make it cover not only drivers
        self.constructors = constructors
        self.engines = engines
        self.tracks = tracks

        self.tracksRetirementFactor = {}

    def getGaElo(self, driverId, gridPosition, trackId):
        gridAdjustment = self.tracks[trackId] * self.getGridAdjustment(gridPosition)

        return (self.drivers[driverId].rating)*DRIVER_WEIGHTING + (self.drivers[driverId].constructor.rating)*CONSTRUCTOR_WEIGHTING + (self.drivers[driverId].constructor.engine.rating)*ENGINE_WEIGHTING + gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getGaEloWithTrackAlpha(self, driverId, gridPosition, trackId, alphaAdjustment):
        gridAdjustment = (self.tracks[trackId] + alphaAdjustment) * self.getGridAdjustment(gridPosition)

        return (self.drivers[driverId].rating)*DRIVER_WEIGHTING + (self.drivers[driverId].constructor.rating)*CONSTRUCTOR_WEIGHTING + (self.drivers[driverId].constructor.engine.rating)*ENGINE_WEIGHTING + gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getBaseRetirementProbability(self, trackId):
        return BASE_RETIREMENT_PROBABILITY

    def getGridAdjustment(self, gridPosition):
        return (10.5 - gridPosition) * GRID_ADJUSTMENT_COEFFICIENT

    def getExpectedScore(self, a, b):
        '''Returns a's expected score against b. A float value between 0 and 1'''
        return 1 / (1 + 10 ** ((b - a) / 400))

    def adjustEloRating(self, driverId, adjustment):
        self.drivers[driverId].rating += (adjustment * K_FACTOR) # TODO check if this is correct

    def adjustEloRatingConstructor(self, constructor, adjustment):
        constructor.rating += (adjustment * K_FACTOR) # TODO check if this is correct

    def adjustEloRatingEngine(self, engine, adjustment):
        engine.rating += (adjustment * K_FACTOR) # TODO check if this is correct

class EloConstructor:
    def __init__(self, name, engine):
        self.name = name
        self.engine = engine
        self.rating = 2200  # Default rating



class EloEngine:
    def __init__(self, name):
        self.name = name
        self.rating = 2200 # Default rating



class EloRaceModelGenerator:
    def __init__(self, seasonsData, raceResultsData, driversData, constructorsData, enginesData):
        self.seasonsData = seasonsData
        self.raceResultsData = raceResultsData
        self.driversData = driversData
        self.constructorsData = constructorsData
        self.enginesData = enginesData
        self.model = None

    def getModel(self):
        if not self.model:
            raise ValueError("Model not generated yet")
        return self.model

    def generateModel(self):
        self.model = EloRaceModel({}, {}, {}, {})
        for year, season in self.seasonsData.items():  # Read every season:
            self._updateModelsForYear(season)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)

            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData:
                    resultsForRace = self.raceResultsData[raceId]
                    self._addNewDriversAndConstructors(resultsForRace, year)
                    self._addNewTrack(data.circuitId)

                  #  results = {}
                    #gaElos = {}
                    driverIds = [x["driverId"] for x in resultsForRace]
                    eloAdjustments = ()
                    eloAdjustmentsSum = 0
                    setEloAdjustmentsSum = False
                    for alphaAdjustment in range(-0.25, 0.26, 0.25):
                        results = {}
                        gaElos = {}
                        for index, res in enumerate(resultsForRace):
                            results[res["driverId"]] = res["position"]
                            gaElos[res["driverId"]] = self.model.getGaEloWithTrackAlpha(res["driverId"], res["grid"], data.circuitId, alphaAdjustment)
                        curEloAdjustments = self._calculateEloAdjustments(driverIds, gaElos, results)
                        curEloAdjustmentsSum = 0
                        for i in range(len(curEloAdjustments[0])):
                            curEloAdjustmentsSum += curEloAdjustments[0][i]
                        for i in range(len(curEloAdjustments[1])):
                            curEloAdjustmentsSum += curEloAdjustments[1][i]
                        for i in range(len(curEloAdjustments[2])):
                            curEloAdjustmentsSum += curEloAdjustments[2][i]

                        if curEloAdjustmentsSum < eloAdjustmentsSum or not setEloAdjustmentsSum:
                            setEloAdjustmentsSum = True
                            eloAdjustmentsSum = curEloAdjustmentsSum
                            eloAdjustments = curEloAdjustments

                    #for index, res in enumerate(resultsForRace):
                      #  results[res["driverId"]] = res["position"]
                      #  gaElos[res["driverId"]] = self.model.getGaElo(res["driverId"], res["grid"], data.circuitId)

                    # For each matchup, calculate expected score and real score. Put results to special data structure
                  #  driverIds = [x["driverId"] for x in resultsForRace]
                    #eloAdjustments = self._calculateEloAdjustments(driverIds, gaElos, results)
                    retirementCount = 0
                    for driverId in driverIds:
                        if results[driverId] is None:
                            self.model.adjustEloRating(driverId, RETIREMENT_PENALTY)
                            retirementCount += 1
                        self.model.adjustEloRating(driverId, eloAdjustments[driverId] + FINISHING_BONUS)

                    # Adjust the retirement factor for this track
                    retirementFrac = retirementCount / driverIds
                    if self.model.tracksRetirementFactor[data.circuitId] == None:
                        self.model.tracksRetirementFactor[data.cirCuitId] = retirementFrac
                    else:
                        oldValue = self.model.tracksRetirementFactor[data.circuitId]
                        self.model.tracksRetirementFactor[data.circuitId] += (retirementFrac - oldValue) * RETIREMENT_PROBABILITY_CHANGE_WEIGHT
                        
                    # TODO Adjust circuit ALPHA

    def generatePredictions(self):
        self.model = EloRaceModel({}, {}, {}, {})
        predictions = []
        for year, season in self.seasonsData.items():  # Read every season:
            self._updateModelsForYear(season)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)

            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData:
                    resultsForRace = self.raceResultsData[raceId]
                    self._addNewDriversAndConstructors(resultsForRace, year)
                    self._addNewTrack(data.circuitId)

                    results = {}
                    gaElos = {}
                    for index, res in enumerate(resultsForRace):
                        results[res["driverId"]] = res["position"]
                        gaElos[res["driverId"]] = self.model.getGaElo(res["driverId"], res["grid"], data.circuitId)

                    # Generate predictions:
                    sortedGaElos = [(driverId, gaElo) for (driverId, gaElo) in gaElos.items()]
                    sortedGaElos.sort(key=lambda x: x[1], reverse=True)
                    if sortedGaElos:
                        predictions.append([x[0] for x in sortedGaElos])

                    # For each matchup, calculate expected score and real score. Put results to special data structure
                    driverIds = [x["driverId"] for x in resultsForRace]
                    # Some drivers may retire without finishing the race,
                    retirementPercentage = self.model.getRetirementProbability(data.circuitId) * 100
                    for driverId in driverIds:
                        retirementRoll = randint(1, 100)
                        if retirementRoll <= 5:
                            # This driver has retired
                            results[driverId] = None

                    eloAdjustments = self._calculateEloAdjustments(driverIds, gaElos, results)
                    for driverId in driverIds:
                        if results[driverId] is None:
                            self.model.adjustEloRating(driverId, RETIREMENT_PENALTY)
                        self.model.adjustEloRating(driverId, eloAdjustments[0][driverId] + FINISHING_BONUS)

                    for constructor in eloAdjustments[1]:
                        self.model.adjustEloRatingConstructor(constructor, eloAdjustments[1][constructor] + FINISHING_BONUS)

                    for engine in eloAdjustments[2]:
                        self.model.adjustEloRatingConstructor(engine, eloAdjustments[2][engine] + FINISHING_BONUS)
                    # TODO Adjust circuit ALPHA

        return predictions

    def _updateModelsForYear(self, season):
        '''Resolves team name changes'''
        # Updating list of engines and constructors:
        for new, old in season.teamChanges.items():
            self.model.constructors[new] = self.model.constructors[old]
            self.model.constructors[new].name = self.constructorsData[new]

        for cId, engineId in season.constructorEngines.items():
            # Check that the constructor and engine exist
            if engineId not in self.model.engines:
                self.model.engines[engineId] = EloEngine(self.enginesData[engineId])
            if cId not in self.model.constructors:
                self.model.constructors[cId] = EloConstructor(self.constructorsData[cId], None)
            # Assign it its engine
            self.model.constructors[cId].engine = self.model.engines[engineId]

    def _updateModelsAtEndOfYear(self, season):
        # Delete old, unused constructors
        for new, old in season.teamChanges.items():
            del self.model.constructors[old]

        # Regress all powers towards the mean
        # TODO

    def _addNewDriversAndConstructors(self, resultsForRace, year):
        for res in resultsForRace:
            if res["driverId"] not in self.model.drivers:
                self.model.drivers[res["driverId"]] = EloDriver(self.driversData[res["driverId"]], res["constructorId"])
                if year > 2003:
                    self.model.drivers[res["driverId"]].rating = ROOKIE_DRIVER_RATING
            if self.model.drivers[res["driverId"]].constructor is not self.model.constructors[res["constructorId"]]:
                self.model.drivers[res["driverId"]].constructor = self.model.constructors[res["constructorId"]]

    def _addNewTrack(self, circuitId):
        if circuitId not in self.model.tracks:
            self.model.tracks[circuitId] = 1

    def _calculateEloAdjustments(self, driverIds, gaElos, results):
        driverAdjustments = {}
        engineAdjustments = {}
        constructorAdjustments = {}
        for i in range(len(driverIds)):
            for k in range(i+1, len(driverIds)):
                if driverIds[i] not in driverAdjustments:
                    driverAdjustments[driverIds[i]] = 0
                if driverIds[k] not in driverAdjustments:
                    driverAdjustments[driverIds[k]] = 0

                if self.model.drivers[driverIds[i]].constructor not in constructorAdjustments:
                    constructorAdjustments[self.model.drivers[driverIds[i]].constructor] = 0
                if self.model.drivers[driverIds[k]].constructor not in constructorAdjustments:
                    constructorAdjustments[self.model.drivers[driverIds[k]].constructor] = 0

                if self.model.drivers[driverIds[i]].constructor.engine not in engineAdjustments:
                    engineAdjustments[self.model.drivers[driverIds[i]].constructor.engine] = 0
                if self.model.drivers[driverIds[k]].constructor.engine not in engineAdjustments:
                    engineAdjustments[self.model.drivers[driverIds[k]].constructor.engine] = 0

                if results[driverIds[i]] is not None and results[driverIds[k]] is not None:
                    headToHeadResult = 1 if results[driverIds[i]] < results[driverIds[k]] else 0
                    expectedScore = self.model.getExpectedScore(gaElos[driverIds[i]], gaElos[driverIds[k]])
                    driverAdjustments[driverIds[i]] += headToHeadResult - expectedScore
                    driverAdjustments[driverIds[k]] += expectedScore - headToHeadResult

                    constructorAdjustments[self.model.drivers[driverIds[i]].constructor] += headToHeadResult - expectedScore
                    constructorAdjustments[self.model.drivers[driverIds[k]].constructor] += expectedScore - headToHeadResult

                    engineAdjustments[self.model.drivers[driverIds[i]].constructor.engine] += headToHeadResult - expectedScore
                    engineAdjustments[self.model.drivers[driverIds[k]].constructor.engine] += expectedScore - headToHeadResult

        return (driverAdjustments, constructorAdjustments, engineAdjustments)
