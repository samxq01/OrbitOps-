"""OrbitOps telemetry mnemonics and physical constants."""

from typing import Final

# Telemetry Mnemonics
MNEMONIC_PWR_BUS_V: Final[str] = "PWR_BUS_V"
MNEMONIC_PWR_SOLAR_W: Final[str] = "PWR_SOLAR_W"
MNEMONIC_BATT_SOC: Final[str] = "BATT_SOC"
MNEMONIC_BATT_TEMP_C: Final[str] = "BATT_TEMP_C"
MNEMONIC_BATT_CURRENT_A: Final[str] = "BATT_CURRENT_A"

MNEMONIC_TEMP_BUS_C: Final[str] = "TEMP_BUS_C"
MNEMONIC_TEMP_PL_C: Final[str] = "TEMP_PL_C"
MNEMONIC_TEMP_RADIO_C: Final[str] = "TEMP_RADIO_C"
MNEMONIC_HEATER_STATUS: Final[str] = "HEATER_STATUS"

MNEMONIC_ATT_ROLL_DEG: Final[str] = "ATT_ROLL_DEG"
MNEMONIC_ATT_PITCH_DEG: Final[str] = "ATT_PITCH_DEG"
MNEMONIC_ATT_YAW_DEG: Final[str] = "ATT_YAW_DEG"
MNEMONIC_ATT_RATE_DPS: Final[str] = "ATT_RATE_DPS"
MNEMONIC_ADCS_MODE: Final[str] = "ADCS_MODE"

MNEMONIC_RF_CARRIER_LOCK: Final[str] = "RF_CARRIER_LOCK"
MNEMONIC_RF_SNR_DB: Final[str] = "RF_SNR_DB"
MNEMONIC_RF_TX_POWER_W: Final[str] = "RF_TX_POWER_W"
MNEMONIC_RF_DOPPLER_HZ: Final[str] = "RF_DOPPLER_HZ"

MNEMONIC_PL_STATUS: Final[str] = "PL_STATUS"
MNEMONIC_PL_POWER_W: Final[str] = "PL_POWER_W"
MNEMONIC_PL_STORAGE_MB: Final[str] = "PL_STORAGE_MB"

# Virtual NORAD IDs (Fictional educational catalog numbers in 99xxx block)
VIRTUAL_NORAD_ALPHA: Final[int] = 99101
VIRTUAL_NORAD_BETA: Final[int] = 99102
VIRTUAL_NORAD_GAMMA: Final[int] = 99103

# Physical boundaries and constraints
EARTH_RADIUS_KM: Final[float] = 6371.0
SOLAR_CONSTANT_W_M2: Final[float] = 1361.0

# Physical validation ranges
MIN_BUS_VOLTAGE_V: Final[float] = 18.0
MAX_BUS_VOLTAGE_V: Final[float] = 36.0
MIN_BATTERY_SOC_PCT: Final[float] = 0.0
MAX_BATTERY_SOC_PCT: Final[float] = 100.0
MIN_TEMPERATURE_C: Final[float] = -100.0
MAX_TEMPERATURE_C: Final[float] = 120.0
MIN_ELEVATION_DEG: Final[float] = 0.0
MAX_ELEVATION_DEG: Final[float] = 90.0
