Wire format: message framing and (de)serialization. Keep this free of I/O and connection
lifecycle code - pure encode/decode functions are what you fuzz-test.
