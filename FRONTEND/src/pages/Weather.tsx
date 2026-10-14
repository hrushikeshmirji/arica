import { useState } from "react"
import {
  CloudSun,
  Thermometer,
  Droplets,
  Wind,
  Sun,
  CloudRain,
  Compass,
  Search,
  MapPin,
  RefreshCw,
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
} from "lucide-react"
import { useWeather } from "../contexts/WeatherContext"
import { useLanguage } from "../contexts/LanguageContext"

export default function Weather() {
  const { t } = useLanguage()
  const { weatherState, refreshLocationWeather, searchCity } = useWeather()
  const [cityInput, setCityInput] = useState("")

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!cityInput.trim()) return
    await searchCity(cityInput.trim())
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header & Location Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-foreground">{t("weather.title", "Weather Intelligence")}</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("weather.subtitle", "Real-time microclimate analytics and disease risk forecasting")}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <form onSubmit={handleSearch} className="flex items-center gap-2 bg-card border border-border rounded-xl px-3 py-2 w-full sm:w-72">
            <input
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              placeholder={t("weather.search_placeholder", "Search city (e.g. Madikeri, Bengaluru)...")}
              className="bg-transparent border-none outline-none text-xs text-foreground placeholder-muted-foreground flex-1"
            />
            <button type="submit" className="p-1 rounded-lg hover:bg-muted text-primary font-bold text-xs flex items-center gap-1" title="Search City">
              <Search size={16} />
            </button>
          </form>

          <button
            onClick={refreshLocationWeather}
            disabled={weatherState.status === "LOADING"}
            className="btn-primary text-xs w-full sm:w-auto flex items-center justify-center gap-2 shadow-sm"
          >
            {weatherState.status === "LOADING" ? <RefreshCw size={14} className="animate-spin" /> : <MapPin size={14} />}
            <span>{t("weather.use_location", "Use Current Location")}</span>
          </button>
        </div>
      </div>

      {/* Quick Plantation Location Presets */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] text-muted-foreground font-semibold">Key Plantations:</span>
        {["Madikeri", "Shivamogga", "Mangaluru", "Chikkamagaluru", "Sirsi"].map((city) => (
          <button
            key={city}
            onClick={() => searchCity(city)}
            className="px-2.5 py-1 rounded-lg bg-card border border-border text-[11px] font-medium text-foreground hover:border-primary hover:text-primary transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            {city}
          </button>
        ))}
      </div>

      {/* 5-STATE WEATHER CONTENT */}
      {weatherState.status === "UNREQUESTED" && (
        <div className="bg-card rounded-2xl border border-dashed border-border p-12 text-center max-w-xl mx-auto my-8 space-y-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto shadow-md">
            <MapPin size={32} />
          </div>
          <h2 className="text-lg font-bold text-foreground">{t("weather.location_required", "Location Access Required")}</h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {t("weather.location_required_desc", "Grant browser location access or search your plantation city above to load live temperature, humidity, rainfall, and fungal risk metrics.")}
          </p>
          <button onClick={refreshLocationWeather} className="btn-primary text-xs mx-auto flex items-center gap-2">
            <MapPin size={14} /> {t("weather.enable_location", "Enable Live Location")}
          </button>
        </div>
      )}

      {weatherState.status === "DENIED" && (
        <div className="bg-card rounded-2xl border border-warning/30 p-12 text-center max-w-xl mx-auto my-8 space-y-4">
          <div className="w-16 h-16 rounded-full bg-warning/10 text-warning flex items-center justify-center mx-auto">
            <AlertCircle size={32} />
          </div>
          <h2 className="text-lg font-bold text-foreground">{t("weather.location_denied", "Location Access Denied")}</h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {t("weather.location_denied_desc", "Location permission was denied in your browser. You can search your city manually in the search bar above.")}
          </p>
          <button onClick={() => searchCity("Madikeri")} className="btn-primary text-xs mx-auto flex items-center gap-2">
            <MapPin size={14} /> Load Default (Madikeri)
          </button>
        </div>
      )}

      {weatherState.status === "LOADING" && (
        <div className="bg-card rounded-2xl border border-border p-12 text-center max-w-xl mx-auto my-8 space-y-4 skeleton-pulse">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin mx-auto" />
          <p className="text-sm font-bold text-foreground">{t("weather.loading", "Loading Microclimate Weather Data...")}</p>
        </div>
      )}

      {weatherState.status === "ERROR" && (
        <div className="bg-card rounded-2xl border border-danger/30 p-12 text-center max-w-xl mx-auto my-8 space-y-4">
          <div className="w-16 h-16 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
            <AlertTriangle size={32} />
          </div>
          <h2 className="text-lg font-bold text-foreground">{t("weather.service_unavailable", "Weather Service Unavailable")}</h2>
          <p className="text-xs text-muted-foreground leading-relaxed">{weatherState.message}</p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button onClick={() => searchCity("Madikeri")} className="btn-primary text-xs flex items-center gap-2">
              <MapPin size={14} /> Load Default (Madikeri)
            </button>
            <button onClick={refreshLocationWeather} className="btn-secondary text-xs flex items-center gap-2">
              <RefreshCw size={14} /> {t("dash.retry_conn", "Retry Connection")}
            </button>
          </div>
        </div>
      )}

      {weatherState.status === "POPULATED" && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="bg-card rounded-2xl border border-border p-6 shadow-sm relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                  <MapPin size={14} className="text-primary" />
                  <span>{weatherState.data.city}, {weatherState.data.region}</span>
                  <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold">
                    {t("weather.live_badge", "Live")}
                  </span>
                </div>

                <div className="flex items-baseline gap-4 mt-3">
                  <span className="text-5xl font-extrabold text-foreground tracking-tight">
                    {weatherState.data.temperature}°C
                  </span>
                  <span className="text-lg font-bold text-muted-foreground">{weatherState.data.condition}</span>
                </div>

                <div className="text-xs text-muted-foreground mt-2">
                  {t("weather.last_updated", "Last updated at")} {weatherState.data.lastUpdated}
                </div>
              </div>

              {/* Disease Risk Warning */}
              <div className={`p-4 rounded-xl border max-w-xs ${
                weatherState.data.riskLevel === "High"
                  ? "bg-danger/10 border-danger/20 text-danger"
                  : "bg-warning/10 border-warning/20 text-warning"
              }`}>
                <div className="flex items-center gap-2 font-bold text-sm mb-1">
                  <ShieldAlert size={18} />
                  <span>{t("weather.risk", "Disease Risk")}: {weatherState.data.riskLevel}</span>
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed">
                  {t("weather.humidity_risk_desc", "Relative humidity significantly impacts fungal spore germination (Anthracnose & Koleroga).")}
                </p>
              </div>
            </div>

            {/* Grid Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-6 pt-6 border-t border-border">
              {[
                { icon: Thermometer, label: t("weather.temp", "Temperature"), val: `${weatherState.data.temperature}°C` },
                { icon: Droplets, label: t("weather.humidity", "Humidity"), val: `${weatherState.data.humidity}%` },
                { icon: Wind, label: t("weather.wind", "Wind Speed"), val: `${weatherState.data.windSpeed} km/h` },
                { icon: CloudRain, label: t("weather.rainfall", "Rainfall"), val: `${weatherState.data.rainfall} mm` },
                { icon: Sun, label: t("weather.uv", "UV Index"), val: `${weatherState.data.uvIndex} / 10` },
                { icon: Compass, label: t("weather.sunrise_label", "Sunrise/Sunset"), val: `${weatherState.data.sunrise}` },
              ].map(({ icon: Icon, label, val }) => (
                <div key={label} className="p-3 rounded-xl bg-muted/30 border border-border text-center">
                  <Icon size={18} className="mx-auto text-primary mb-1" />
                  <div className="text-sm font-extrabold text-foreground">{val}</div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 5-Day Forecast Grid */}
          <div>
            <h2 className="text-base font-bold text-foreground mb-4">{t("weather.forecast_5day", "5-Day Microclimate Forecast")}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
              {weatherState.data.forecast.map((f) => (
                <div key={f.day} className="bg-card rounded-xl border border-border p-4 text-center card-hover">
                  <div className="text-xs font-bold text-foreground mb-2">{f.day}</div>
                  <CloudSun size={24} className="mx-auto text-warning mb-2" />
                  <div className="text-sm font-extrabold text-foreground">{f.tempMax}° / {f.tempMin}°</div>
                  <div className="text-[11px] text-muted-foreground mt-1">{f.condition}</div>
                  <div className="text-[10px] font-bold text-primary mt-2">{t("weather.rain_prefix", "Rain")}: {f.rainProb}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
