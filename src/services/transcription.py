import uuid
import http
import time
import requests
import json

from fastapi import Response
from botocore.exceptions import ClientError

from src.utils.aws.s3 import AWSS3Client
from src.utils.aws.transcribe import AWSTranscribeClient


class TranscriptionService:
    POLL_INTERVAL_SEC = 5  # 5sec  x 3%/sec

    def generate_file_uri(self, bucket_name: str, filename: str, extension: str):
        # NOTE - Can add subbuckets in the future
        return f"s3://{bucket_name}/{filename}.{extension}"

    async def get_all_transcriptions(self, transcribe_client, job_name: str):
        job_result = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        transciption = job_result["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        return transciption

    async def poll_transcription_job(self, transcribe_client, job_name: str):
        max_tries = 60
        is_done = False

        while max_tries > 0:
            max_tries -= 1
            job_result = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            job_status = job_result["TranscriptionJob"]["TranscriptionJobStatus"]

            if job_status in ["COMPLETED", "FAILED"]:
                print(f"Job {job_name} is {job_status}.")

                if job_status == "COMPLETED":
                    is_done = True
                    # print(
                    #   f"Download the transcript from\n"
                    #   f"\t{job_result['TranscriptionJob']['Transcript']['TranscriptFileUri']}."
                    # )
                break
            else:
                print(
                    f"Waiting for Transcription Job: {job_name}. Current status is {job_status}."
                )

            # Set interval to poll job status
            time.sleep(self.POLL_INTERVAL_SEC)

        if not is_done:
            return TimeoutError("Timeout when polling the transcription results")

        return job_result

    async def transcribe_file(
        self,
        transcribe_client: any,
        job_name: str,
        file_uri: str,
        file_format: str,
        language_code="id-ID",
    ):
        try:
            transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": file_uri},
                MediaFormat=file_format,
                LanguageCode=language_code,
            )

            job_result = await self.poll_transcription_job(
                transcribe_client=transcribe_client, job_name=job_name
            )

      return job_result
    except TimeoutError:
      return TimeoutError("Timeout when polling the transcription results")
    except ClientError:
        return ClientError("Transcription Job failed.", operation_name="start_transcription_job")
    
  