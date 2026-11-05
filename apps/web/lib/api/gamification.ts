import type { Gamification } from "@/types/api";

import { api } from "./client";

export const getGamificationMe = () => api.get<Gamification>("/gamification/me").then((r) => r.data);
