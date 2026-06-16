import { UserToken } from "../entities/Auth";

export interface AuthRepository {
    login(username: string, password: string): Promise<UserToken>;
}