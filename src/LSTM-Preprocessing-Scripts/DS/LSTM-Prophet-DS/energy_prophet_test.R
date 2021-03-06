library(forecast)
library(xts)
library(prophet)
set.seed(1234)

df_train <- read.csv("solar_train.txt", header = FALSE)

OUTPUT_DIR = "Mean_Moving_window"
input_size = 24*1.25
max_forecast_horizon <- 24
seasonality_period_1 <- 24
seasonality_period_2 <- 168
seasonality_period_3 <- 8766

start_time <- Sys.time()

for (idr in 1 : nrow(df_train)) {
  print(idr)
  OUTPUT_PATH = paste(OUTPUT_DIR, "energy_prophet_test", sep = '/')
  OUTPUT_PATH = paste(OUTPUT_PATH, max_forecast_horizon, sep = '')
  OUTPUT_PATH = paste(OUTPUT_PATH, 'i', input_size, sep = '')
  OUTPUT_PATH = paste(OUTPUT_PATH, 'txt', sep = '.')
  
  time_series_data <- as.numeric(df_train[idr,])
  time_series_mean <- mean(time_series_data)
  
  time_series_data <- time_series_data/(time_series_mean)
  
  time_series_log <- log(time_series_data + 1)
  time_series_length = length(time_series_log)
  
  ts <- seq(from = as.POSIXct("2010-01-01 00:00"), length.out =  time_series_length, by = "hour")
  history <- data.frame(ds = ts, y = time_series_log)
  
  # apply stl
  stl_result = tryCatch({
    sstl = prophet(history, daily.seasonality = TRUE, weekly.seasonality = TRUE, yearly.seasonality = TRUE)
    sstl_comp = predict(sstl)
    seasonal_vect = sstl_comp$daily + sstl_comp$weekly + sstl_comp$yearly
    levels_vect = sstl_comp$trend
    residuals = (time_series_log - sstl_comp$yhat)
    values_vect = residuals + (levels_vect)
    cbind(seasonal_vect, levels_vect, values_vect)
  }, error = function(e) {
    seasonal_vect = rep(0, length(time_series_length))
    levels_vect = time_series_log
    values_vect = time_series_log
    cbind(seasonal_vect, levels_vect, values_vect)
  })
  
  future_start <-  ts[time_series_length] + 3600
  
  future <- data.frame(ds = seq(from = future_start , length.out = 24, by = "hour"))
  m <- prophet(history, daily.seasonality = TRUE, weekly.seasonality = TRUE, yearly.seasonality = TRUE)
  forecast_prophet <- predict(m,future)
  
  seasonality <- forecast_prophet$daily + forecast_prophet$weekly + forecast_prophet$yearly
  
  input_windows = embed(stl_result[1 : time_series_length , 3], input_size)[, input_size : 1]
  level_values = stl_result[input_size : time_series_length, 2]
  input_windows = input_windows - level_values
  
  sav_df = matrix(NA, ncol = (4 + input_size + max_forecast_horizon), nrow = length(level_values))
  sav_df = as.data.frame(sav_df)
  
  sav_df[, 1] = paste(idr - 1, '|i', sep = '')
  sav_df[, 2 : (input_size + 1)] = input_windows
  
  sav_df[, (input_size + 2)] = '|#'
  sav_df[, (input_size + 3)] = time_series_mean
  sav_df[, (input_size + 4)] = level_values
  
  seasonality_windows = matrix(rep(t(seasonality),each=length(level_values)),nrow=length(level_values))
  sav_df[(input_size + 5) : ncol(sav_df)] = seasonality_windows
  
  write.table(sav_df, file = OUTPUT_PATH, row.names = F, col.names = F, sep = " ", quote = F, append = TRUE)
}

end_time <- Sys.time()
print(paste0("Total time", (end_time - start_time)))
