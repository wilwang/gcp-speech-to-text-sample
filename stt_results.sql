CREATE OR REPLACE TABLE sandbox_data.stt_results(
    source_file_uri STRING,
    transcription STRING,
    transcribe_json JSON,
    entity_json JSON,
    sentiment_json JSON
)
