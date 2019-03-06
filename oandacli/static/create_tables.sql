-- sql for streaming and tracking

CREATE TABLE pricing_stream (
  time VARCHAR(30),
  instrument VARCHAR(7),
  json TEXT
);

CREATE INDEX ix_pricing_stream_time ON pricing_stream (time);
CREATE INDEX ix_pricing_stream_inst ON pricing_stream (instrument);

CREATE TABLE transaction_stream (
  time VARCHAR(30),
  instrument VARCHAR(7),
  json TEXT
);

CREATE INDEX ix_transaction_stream_time ON transaction_stream (time);
CREATE INDEX ix_transaction_stream_inst ON transaction_stream (instrument);

CREATE TABLE candle (
  time VARCHAR(30),
  instrument VARCHAR(7),
  openBid DOUBLE PRECISION,
  openAsk DOUBLE PRECISION,
  highBid DOUBLE PRECISION,
  highAsk DOUBLE PRECISION,
  lowBid DOUBLE PRECISION,
  lowAsk DOUBLE PRECISION,
  closeBid DOUBLE PRECISION,
  closeAsk DOUBLE PRECISION,
  volume INTEGER,
  PRIMARY KEY(instrument, time)
);

CREATE INDEX ix_candle_time ON candle (time);
CREATE INDEX ix_candle_inst ON candle (instrument);
