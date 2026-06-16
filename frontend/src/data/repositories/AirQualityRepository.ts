import { Device, SensorLog, Classification, ForecastPrediction } from "@/src/domain/entities/AirQuality";

export interface AirQualityRepository {
    getDevices(token: string): Promise<Device[]>;
    toggleDeviceStatus(deviceId: number, status: boolean, token: string): Promise<Device>;
    getSensorHistory(deviceId: number, limit: number, token: string): Promise<SensorLog[]>;
    getLatestClassification(deviceId: number, token: string): Promise<Classification | null>;
    getHistoryClassification(deviceId: number, limit: number, token: string): Promise<Classification[]>;
    triggerForecast(deviceId: number, token: string): Promise<ForecastPrediction>;
}