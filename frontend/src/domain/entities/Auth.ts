export interface UserToken {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
}

export interface RegisterRequest {
    username: string;
    email: string;
    password: string;
}

export interface RegisterResponse {
    status: string;
    message: string;
    userId?: number;
}