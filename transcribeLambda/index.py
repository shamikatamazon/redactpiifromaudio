import time
import boto3
import os
import subprocess
import shlex
import requests
import json

def handler(event, context):
    
    print(event)
    
    inputKey = event["Records"][0]["s3"]["object"]["key"]
    inputBucket = event["Records"][0]["s3"]["bucket"]["name"]
    
    inputFile = "s3://" + inputBucket + "/" + inputKey
    print(inputFile)
    
    transcribe = boto3.client('transcribe')
    job_name = "job-name-" + str(time.time())
    job_uri = inputFile
    
    transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': job_uri
    },
    ContentRedaction={
      'RedactionType' : "PII",
      'RedactionOutput' : "redacted"
    },
    MediaFormat='mp3',
    LanguageCode='en-US'
    )
    
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("Not ready yet...")
        time.sleep(5)
    print(status)
    
    redactedTimesUrl = status['TranscriptionJob']["Transcript"]['RedactedTranscriptFileUri']
    redactedHttpResponse = requests.get(redactedTimesUrl)
    print(redactedHttpResponse.text)
    
    data = redactedHttpResponse.json()
    print(data)

    redactString = ""

    for i in data['results']['items']:
        #print(i['alternatives'][0]['content'])
        if i['alternatives'][0]['content'] == "[PII]":
            redactString = redactString + "volume=enable='between(t," + i['start_time'] + "," + i['end_time'] + ")':volume=0,"
        
    modifiedRedactedString = "\"" + redactString[:-1] + "\""
    print(modifiedRedactedString)    

    s3_client = boto3.client('s3')
    
    s3_source_signed_url = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': inputBucket, 'Key': inputKey},
        ExpiresIn=100)
    
    ffmpeg_cmd = "/opt/bin/ffmpeg -i " + s3_source_signed_url + " -f mp3 -af " + modifiedRedactedString + " -"
    command1 = shlex.split(ffmpeg_cmd)
    print(command1)
    p1 = subprocess.run(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p1)
    
    outputBucketName = os.environ['targetS3']
    print(outputBucketName)
    outputkey = inputKey + "_redacted.mp3"
    
    resp = s3_client.put_object(Body=p1.stdout, Bucket=outputBucketName, Key=outputkey)