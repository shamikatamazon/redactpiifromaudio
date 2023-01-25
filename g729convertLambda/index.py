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
    
    
    s3_client = boto3.client('s3')
    
    #inputFile = "s3://" + inputBucket + "/" + inputKey
    #inputFile = "s3://g729inputfiles/g729-sample-2.wav"
    
    s3_source_signed_url = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': inputBucket, 'Key': inputKey},
        ExpiresIn=100)
    
    
    ffmpeg_cmd = "/opt/bin/ffmpeg -i " + s3_source_signed_url + " -f mp3 -"
    
    command1 = shlex.split(ffmpeg_cmd)
    print(command1)
    p1 = subprocess.run(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p1)
    print("audio output")
    
    outputBucketName = os.environ['targetS3']
    print(outputBucketName)
    outputkey = inputKey + "_converted.mp3"
    
    resp = s3_client.put_object(Body=p1.stdout, Bucket=outputBucketName, Key=outputkey)
    print(resp)
    
    #conversion done - starting transcribe
    
    
    transcribe = boto3.client('transcribe')
    job_name = "job-name-" + str(time.time())
    job_uri = "s3://" + outputBucketName  + "/" + outputkey
    
    transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': job_uri
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
    
    redactedTimesUrl = status['TranscriptionJob']["Transcript"]['TranscriptFileUri']
    redactedHttpResponse = requests.get(redactedTimesUrl)
    print(redactedHttpResponse.text)
    
    data = redactedHttpResponse.json()
    print(data)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
