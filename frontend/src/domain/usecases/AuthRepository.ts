import { RegisterRequest, RegisterResponse, UserToken } from "../entities/Auth";

export interface AuthRepository {
    login(username: string, password: string): Promise<UserToken>;
    register(data: RegisterRequest): Promise<RegisterResponse>;
}