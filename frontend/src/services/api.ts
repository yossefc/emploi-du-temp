import axios, { AxiosInstance } from 'axios';
import { config } from '../config';

const API_BASE_URL = `${config.api.baseUrl}/api/v1`;

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor pour ajouter le token d'authentification
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor pour gérer les erreurs
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expiré, essayer de rafraîchir
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.data.access_token);
              
              // Réessayer la requête originale
              error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
              return this.api.request(error.config);
            }
          } catch (refreshError) {
            // Échec du rafraîchissement, rediriger vers login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(email: string, password: string) {
    // Le backend attend 'username' et format URLSearchParams
    const params = new URLSearchParams();
    params.append('username', email);  // Note: 'username', pas 'email'
    params.append('password', password);
    
    return this.api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
  }

  async register(userData: any) {
    return this.api.post('/auth/register', userData);
  }

  async refreshToken(refreshToken: string) {
    return this.api.post('/auth/refresh', { refresh_token: refreshToken });
  }

  async logout() {
    return this.api.post('/auth/logout');
  }

  // Teachers endpoints
  async getTeachers() {
    // Temporarily use test endpoint without authentication
    return this.api.get('/teachers-test');
  }

  async getTeacher(id: number) {
    return this.api.get(`/teachers/${id}`);
  }

  async createTeacher(teacherData: any) {
    // Temporarily use test endpoint without authentication
    return this.api.post('/teachers-test', teacherData);
  }

  async updateTeacher(id: number, teacherData: any) {
    return this.api.put(`/teachers/${id}`, teacherData);
  }

  async deleteTeacher(id: number) {
    return this.api.delete(`/teachers/${id}`);
  }

  // Subjects endpoints
  async getSubjects() {
    return this.api.get('/subjects');
  }

  async getSubject(id: number) {
    return this.api.get(`/subjects/${id}`);
  }

  async createSubject(subjectData: any) {
    return this.api.post('/subjects', subjectData);
  }

  async updateSubject(id: number, subjectData: any) {
    return this.api.put(`/subjects/${id}`, subjectData);
  }

  async deleteSubject(id: number) {
    return this.api.delete(`/subjects/${id}`);
  }

  // Classes endpoints
  async getClasses() {
    return this.api.get('/classes');
  }

  async getClass(id: number) {
    return this.api.get(`/classes/${id}`);
  }

  async createClass(classData: any) {
    return this.api.post('/classes', classData);
  }

  async updateClass(id: number, classData: any) {
    return this.api.put(`/classes/${id}`, classData);
  }

  async deleteClass(id: number) {
    return this.api.delete(`/classes/${id}`);
  }

  // Rooms endpoints
  async getRooms() {
    return this.api.get('/rooms');
  }

  async getRoom(id: number) {
    return this.api.get(`/rooms/${id}`);
  }

  async createRoom(roomData: any) {
    return this.api.post('/rooms', roomData);
  }

  async updateRoom(id: number, roomData: any) {
    return this.api.put(`/rooms/${id}`, roomData);
  }

  async deleteRoom(id: number) {
    return this.api.delete(`/rooms/${id}`);
  }

  // Constraints endpoints
  async getConstraints() {
    return this.api.get('/constraints');
  }

  async createConstraint(constraintData: any) {
    return this.api.post('/constraints', constraintData);
  }

  async updateConstraint(id: number, constraintData: any) {
    return this.api.put(`/constraints/${id}`, constraintData);
  }

  async deleteConstraint(id: number) {
    return this.api.delete(`/constraints/${id}`);
  }

  // Schedule endpoints
  async getSchedules() {
    return this.api.get('/schedules');
  }

  async getSchedule(id: number) {
    return this.api.get(`/schedules/${id}`);
  }

  async generateSchedule(params: any) {
    return this.api.post('/schedules/generate', params);
  }

  async updateScheduleEntry(scheduleId: number, entryData: any) {
    return this.api.put(`/schedules/${scheduleId}/entries`, entryData);
  }

  async exportSchedule(id: number, format: 'pdf' | 'excel' | 'ics') {
    return this.api.get(`/schedules/${id}/export`, {
      params: { format },
      responseType: 'blob'
    });
  }

  // AI Agent endpoints
  async sendAIMessage(message: string, context?: any) {
    return this.api.post('/ai/chat', { message, context });
  }

  async parseConstraints(text: string) {
    return this.api.post('/ai/parse-constraints', { text });
  }

  async getSuggestions(scheduleId: number) {
    return this.api.get(`/ai/suggestions/${scheduleId}`);
  }

  async explainConflict(conflictId: number) {
    return this.api.get(`/ai/explain-conflict/${conflictId}`);
  }
}

const apiService = new ApiService();
export default apiService; 