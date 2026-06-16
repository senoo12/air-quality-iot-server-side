export interface Device {
    id: number;
    deviceName: string;
    userId: number;
    isActive: boolean;
}

export interface SensorLog {
    id: number;
    timestamp: string;
    temperature: number;
    humidity: number;
    mq135Raw: number;
    co: number;
    nh3: number;
    co2: number;
    acetone: number;
}

export interface Classification {
    id: number;
    status: "Good" | "Moderate" | "Bad";
    createdAt: string;
}

export interface ForecastPrediction {
    id: number;
    status: "Good" | "Moderate" | "Bad";
    targetTime: string;
    targetDate: string;
    confidence: number;
    createdAt: string;
}