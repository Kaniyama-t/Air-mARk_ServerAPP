import subprocess

def returnUserInfo(userName, TwitterID, FacebookURL, GithubID, threeDObjectURL):
    # JSONに整形
    return {
        "name": userName,
        "TwitterID": TwitterID,
        "FacebookURL": FacebookURL,
        "GithubID": GithubID,
        "3DObjURL": threeDObjectURL
    }

def convert3DFileToSfb(filePath, outputFolder):
    result=subprocess.check_output(["/home/hsui2x/public_html/google-ar-asset-converter/sceneform_sdk/linux/converter","-a","-d","--mat","/home/hsui2x/public_html/google-ar-asset-converter/sceneform_sdk/default_materials/fbx_material.sfm","--outdir" , outputFolder , filePath])
    print(result)
    outputObjPath = outputFolder + filePath[(filePath.rfind('/')):(filePath.rfind('.'))] + ".sfb"
    print(outputObjPath)
    return outputFolder


convert3DFileToSfb("/home/hsui2x/public_html/google-ar-asset-converter/input/Ball_FBX.fbx","/home/hsui2x/public_html/google-ar-asset-converter/output")
