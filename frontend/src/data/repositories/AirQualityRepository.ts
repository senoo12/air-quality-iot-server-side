import { Device, SensorLog, Classification, ForecastPrediction } from "@/src/domain/entities/AirQuality";

export interface UserDropdownEntity {
    id: number;
    username: string;
}

export interface AirQualityRepository {
    getDevices(token: string): Promise<Device[]>;
    toggleDeviceStatus(deviceId: number, status: boolean, token: string): Promise<Device>;
    getSensorHistory(deviceId: number, limit: number, token: string): Promise<SensorLog[]>;
    getLatestClassification(deviceId: number, token: string): Promise<Classification | null>;
    getHistoryClassification(deviceId: number, limit: number, token: string): Promise<Classification[]>;
    triggerForecast(deviceId: number, token: string): Promise<ForecastPrediction>;

    createDevice(deviceName: string, userTargetId: number, token: string): Promise<Device>;
    getAllUsers(token: string): Promise<UserDropdownEntity[]>;
    updateAdminStatus(targetUserId: number, isAdminStatus: boolean, token: string): Promise<{ message: string }>;
}