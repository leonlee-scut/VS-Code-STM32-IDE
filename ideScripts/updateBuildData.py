'''
Update/generate 'buildData.json' file in '.vscode' subfolder from new Makefile.
New Makefile is not updated by this script - it is updated with 'updateMakefile.py' or 'updateWorkspaceSources.py'
'''
import os
import json
import datetime

import utilities as utils
import templateStrings as tmpStr

import updatePaths as pth
import updateMakefile as mkf
import updateWorkspaceSources as wks

__version__ = utils.__version__


class BuildDataStrings():
    cSources = 'cSources'
    asmSources = 'asmSources'

    cIncludes = 'cIncludes'
    asmIncludes = 'asmIncludes'

    cDefines = 'cDefines'
    asmDefines = 'asmDefines'

    cFlags = 'cFlags'
    asmFlags = 'asmFlags'

    buildDirPath = 'buildDir'

    gccInludePath = 'gccInludePath'
    gccExePath = 'gccExePath'

    buildToolsPath = 'buildToolsPath'
    targetExecutablePath = 'targetExecutablePath'

    pythonPath = 'pythonPath'

    openOcdPath = 'openOcdPath'
    openOcdConfig = 'openOcdConfig'

    stm32SvdPath = 'stm32SvdPath'
    stm32SvdFile = 'stm32SvdFile'

    cubeMxProjectPath = 'cubeMxProjectPath'


class BuildData():
    def __init__(self):
        self.mkfStr = mkf.MakefileStrings()
        self.cPStr = wks.CPropertiesStrings()
        self.bStr = BuildDataStrings()

    def prepareBuildData(self):
        '''
        This function is used in all 'update*.py' scripts and makes sure, that buildData with
        a valid tools paths exist. It also updates 'toolsPaths.json' file.

        Returns available, valid build data.
        '''
        paths = pth.UpdatePaths()

        self.checkBuildDataFile()
        buildData = self.getBuildData()
        if self.checkToolsPathFile():  # toolsPaths.json exists
            buildData = self.addToolsPathsData(buildData)
        buildData = paths.verifyExistingPaths(buildData)
        self.createUserToolsFile(buildData)

        return buildData

    def checkBuildDataFile(self):
        '''
        Check if 'buildData.json' file exists. If it does, check if it is a valid JSON file.
        If it doesn't exist, create new according to template.
        '''
        if utils.pathExists(utils.buildDataPath):
            # file exists, check if it loads OK
            try:
                with open(utils.buildDataPath, 'r') as buildDataFile:
                    data = json.load(buildDataFile)

                    print("Existing 'buildData.json' file found.")

            except Exception as err:
                errorMsg = "Invalid 'buildData.json' file. Creating new one. Error:\n"
                errorMsg += "Possible cause: invalid json format or comments (not supported by this scripts). Error:\n"
                errorMsg += str(err)
                print(errorMsg)

                self.createBuildDataFile()

        else:  # 'buildData.json' file does not exist jet, create it according to template string
            self.createBuildDataFile()

    def checkToolsPathFile(self):
        '''
        Returns True if 'toolsPaths.json' file exists and is a valid JSON file.
        If it doesn't exist, delete it and return False.
        '''
        if utils.pathExists(utils.toolsPaths):
            # file exists, check if it loads OK
            try:
                with open(utils.toolsPaths, 'r') as toolsFileHandler:
                    data = json.load(toolsFileHandler)
                    print("Valid 'toolsPaths.json' file found.")
                return True

            except Exception as err:
                errorMsg = "Invalid 'toolsPaths.json' file. Error:\n" + str(err)
                print(errorMsg)

                try:
                    os.remove(utils.toolsPaths)
                    errorMsg = "\tDeleted. New 'toolsPaths.json' will be created on first valid user paths update."
                    print(errorMsg)
                except Exception as err:
                    errorMsg = "\tError deleting 'toolsPaths.json'. Error:\n" + str(err)
                    print(errorMsg)
                return False

        else:  # toolsPaths.json does not exist
            return False

    def createUserToolsFile(self, buildData):
        '''
        Create 'toolsPaths.json' file with current tools absolute paths. 
        '''
        data = {}
        try:
            data["ABOUT1"] = "Common tools paths that are automatically filled in buildData.json."
            data["ABOUT2"] = "Delete/correct this file if paths change on system."
            data[self.bStr.gccExePath] = buildData[self.bStr.gccExePath]
            data[self.bStr.gccInludePath] = buildData[self.bStr.gccInludePath]
            data[self.bStr.buildToolsPath] = buildData[self.bStr.buildToolsPath]
            data[self.bStr.pythonPath] = buildData[self.bStr.pythonPath]
            data[self.bStr.openOcdPath] = buildData[self.bStr.openOcdPath]
            data[self.bStr.openOcdConfig] = buildData[self.bStr.openOcdConfig]
            data[self.bStr.stm32SvdPath] = buildData[self.bStr.stm32SvdPath]
            data[self.bStr.stm32SvdFile] = buildData[self.bStr.stm32SvdFile]

            # dataToWrite = json.dump(data, indent=4, sort_keys=False) # TODO HERE

            with open(utils.toolsPaths, 'w+') as toolsPathsFile:
                json.dump(data, toolsPathsFile, indent=4, sort_keys=False)

            print("'toolsPaths.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'toolsPaths.json' file:\n"
            errorMsg += str(err)
            print("WARNING:", errorMsg)

    def createBuildDataFile(self):
        '''
        Create fresh 'buildData.json' file. 
        '''
        try:
            data = json.loads(tmpStr.buildDataTemplate)
            dataToWrite = json.dumps(data, indent=4, sort_keys=False)

            with open(utils.buildDataPath, 'w+') as buildDataFile:
                buildDataFile.truncate()
                buildDataFile.write(dataToWrite)

            print("New 'buildData.json' file created.")
        except Exception as err:
            errorMsg = "Exception error creating new 'buildData.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def getToolsPathsData(self):
        '''
        Get data from current 'toolsPaths.json' file.
        File existance is previoulsy checked in 'checkToolsPathFile()'.
        '''
        with open(utils.toolsPaths, 'r') as toolsPathsFile:
            data = json.load(toolsPathsFile)

        return data

    def getBuildData(self):
        '''
        Get data from current 'buildData.json' file.
        File existance is previoulsy checked in 'checkBuildDataFile()'.
        '''
        with open(utils.buildDataPath, 'r') as buildDataFile:
            data = json.load(buildDataFile)

        return data

    def addToolsPathsData(self, buildData):
        '''
        If available, add data from 'toolsPaths.json' to buildData
        Returns new data.
        '''
        toolsPathsData = self.getToolsPathsData()
        buildData[self.bStr.gccExePath] = toolsPathsData[self.bStr.gccExePath]
        buildData[self.bStr.gccInludePath] = toolsPathsData[self.bStr.gccInludePath]
        buildData[self.bStr.buildToolsPath] = toolsPathsData[self.bStr.buildToolsPath]
        buildData[self.bStr.pythonPath] = toolsPathsData[self.bStr.pythonPath]
        buildData[self.bStr.openOcdPath] = toolsPathsData[self.bStr.openOcdPath]
        buildData[self.bStr.openOcdConfig] = toolsPathsData[self.bStr.openOcdConfig]
        buildData[self.bStr.stm32SvdPath] = toolsPathsData[self.bStr.stm32SvdPath]
        buildData[self.bStr.stm32SvdFile] = toolsPathsData[self.bStr.stm32SvdFile]

        return buildData

    def addMakefileDataToBuildDataFile(self, buildData, makefileData):
        '''
        This function fills buildData.json file with data from 'Makefile'.
        Returns new data.
        '''
        # sources
        cSources = makefileData[self.mkfStr.cSources]
        buildData[self.bStr.cSources] = cSources

        asmSources = makefileData[self.mkfStr.asmSources]
        buildData[self.bStr.asmSources] = asmSources

        # includes
        cIncludes = makefileData[self.mkfStr.cIncludes]
        buildData[self.bStr.cIncludes] = cIncludes

        asmIncludes = makefileData[self.mkfStr.asmIncludes]
        buildData[self.bStr.asmIncludes] = asmIncludes

        # defines
        cDefines = makefileData[self.mkfStr.cDefines]
        buildData[self.bStr.cDefines] = cDefines

        asmDefines = makefileData[self.mkfStr.asmDefines]
        buildData[self.bStr.asmDefines] = asmDefines

        # compiler flags and paths
        cFlags = makefileData[self.mkfStr.cFlags]
        buildData[self.bStr.cFlags] = cFlags

        asmFlags = makefileData[self.mkfStr.asmFlags]
        buildData[self.bStr.asmFlags] = asmFlags

        # build folder must be always inside workspace folder
        buildDirPath = makefileData[self.mkfStr.buildDir]
        buildData[self.bStr.buildDirPath] = buildDirPath

        # Target executable '.elf' file
        projectName = makefileData[self.mkfStr.projectName]
        targetExecutablePath = utils.getBuildElfFilePath(buildDirPath, projectName)
        buildData[self.bStr.targetExecutablePath] = targetExecutablePath

        return buildData

    def addCubeMxProjectPathToBuildData(self, buildData):
        '''
        If utils.cubeMxProjectFilePath is not None, add/update 'cubeMxProjectPath' field to 'buildData.json'.
        '''
        if utils.cubeMxProjectFilePath is not None:
            buildData[self.bStr.cubeMxProjectPath] = utils.cubeMxProjectFilePath
        return buildData

    def overwriteBuildDataFile(self, data):
        '''
        Overwrite existing 'buildData.json' file with new data.
        '''
        try:
            with open(utils.buildDataPath, 'r+') as buildDataFile:
                data["VERSION"] = __version__
                data["LAST_RUN"] = str(datetime.datetime.now())

                buildDataFile.seek(0)
                buildDataFile.truncate()
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)
                buildDataFile.write(dataToWrite)

            print("'buildData.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'buildData.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    makefile = mkf.Makefile()
    bData = BuildData()

    # Makefile must exist - # point in continuing if Makefile does not exist
    makefile.checkMakefileFile()

    # build data (update tools paths if neccessary)
    buildData = bData.prepareBuildData()

    # data from current Makefile
    makeExePath = buildData[bData.bStr.buildToolsPath]
    gccExePath = buildData[bData.bStr.gccExePath]
    makefileData = makefile.getMakefileData(makeExePath, gccExePath)

    # try to add CubeMX project file path
    buildData = bData.addCubeMxProjectPathToBuildData(buildData)

    buildData = bData.addMakefileDataToBuildDataFile(buildData, makefileData)

    bData.overwriteBuildDataFile(buildData)
