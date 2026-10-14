import React, { createContext, useContext, useState, useEffect, useCallback, useRef, useMemo } from "react"
import {
  getCurrentLocationWeather,
  searchWeatherByCity,
  WeatherState,
} from "../services/weatherService"

interface WeatherContextType {
  weatherState: WeatherState
  refreshLocationWeather: () => Promise<void>
  searchCity: (cityName: string) => Promise<void>
}

const WeatherContext = createContext<WeatherContextType>({
  weatherState: { status: "UNREQUESTED" },
  refreshLocationWeather: async () => undefined,
  searchCity: async () => undefined,
})

export const WeatherProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [weatherState, setWeatherState] = useState<WeatherState>({ status: "LOADING" })
  const requestIdRef = useRef(0)

  const refreshLocationWeather = useCallback(async () => {
    const thisRequestId = ++requestIdRef.current
    setWeatherState({ status: "LOADING" })
    try {
      const res = await getCurrentLocationWeather()
      if (thisRequestId === requestIdRef.current) {
        setWeatherState(res)
      }
    } catch (e) {
      if (thisRequestId === requestIdRef.current) {
        setWeatherState({ status: "ERROR", message: "Failed to fetch weather" })
      }
    }
  }, [])

  const searchCity = useCallback(async (cityName: string) => {
    if (!cityName.trim()) return
    const thisRequestId = ++requestIdRef.current
    setWeatherState({ status: "LOADING" })
    try {
      const res = await searchWeatherByCity(cityName.trim())
      if (thisRequestId === requestIdRef.current) {
        setWeatherState(res)
      }
    } catch (e) {
      if (thisRequestId === requestIdRef.current) {
        setWeatherState({ status: "ERROR", message: "Failed to fetch weather" })
      }
    }
  }, [])

  // Fetch on mount: attempt live location first, fallback gracefully
  useEffect(() => {
    refreshLocationWeather()
  }, [refreshLocationWeather])

  const value = useMemo(
    () => ({ weatherState, refreshLocationWeather, searchCity }),
    [weatherState, refreshLocationWeather, searchCity]
  )

  return (
    <WeatherContext.Provider value={value}>
      {children}
    </WeatherContext.Provider>
  )
}

export const useWeather = () => useContext(WeatherContext)