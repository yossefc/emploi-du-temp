import { rest } from 'msw';
import { 
  generateMockSubjects, 
  generateMockTeachers, 
  generateMockClassGroups, 
  generateMockRooms 
} from '../test-utils';

const API_BASE_URL = 'http://localhost:8000';

// Mock data storage
let mockSubjects = generateMockSubjects(50);
let mockTeachers = generateMockTeachers(30);
let mockClassGroups = generateMockClassGroups(20);
let mockRooms = generateMockRooms(25);

// Helper functions
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const paginate = <T>(data: T[], page: number, limit: number) => {
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const items = data.slice(startIndex, endIndex);
  
  return {
    items,
    total: data.length,
    page,
    limit,
    total_pages: Math.ceil(data.length / limit),
    has_next: endIndex < data.length,
    has_prev: page > 1,
  };
};

const filterData = <T extends Record<string, any>>(
  data: T[], 
  searchQuery?: string,
  isActive?: boolean
) => {
  let filtered = [...data];
  
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    filtered = filtered.filter(item => 
      Object.values(item).some(value => 
        String(value).toLowerCase().includes(query)
      )
    );
  }
  
  if (isActive !== undefined) {
    filtered = filtered.filter(item => item.is_active === isActive);
  }
  
  return filtered;
};

export const handlers = [
  // ============================================================================
  // SUBJECTS API
  // ============================================================================
  
  // Get all subjects
  rest.get(`${API_BASE_URL}/api/v1/subjects`, async (req, res, ctx) => {
    await delay(300); // Simulate network delay
    
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const search = url.searchParams.get('search') || '';
    const isActive = url.searchParams.get('is_active');
    
    const filtered = filterData(mockSubjects, search, isActive === 'true');
    const result = paginate(filtered, page, limit);
    
    return res(ctx.status(200), ctx.json(result));
  }),

  // Get subject by ID
  rest.get(`${API_BASE_URL}/api/v1/subjects/:id`, async (req, res, ctx) => {
    await delay(200);
    
    const { id } = req.params;
    const subject = mockSubjects.find(s => s.id === parseInt(id as string));
    
    if (!subject) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Subject not found' })
      );
    }
    
    return res(ctx.status(200), ctx.json(subject));
  }),

  // Create subject
  rest.post(`${API_BASE_URL}/api/v1/subjects`, async (req, res, ctx) => {
    await delay(400);
    
    const body = await req.json();
    const newSubject = {
      id: Math.max(...mockSubjects.map(s => s.id)) + 1,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    mockSubjects.push(newSubject);
    
    return res(ctx.status(201), ctx.json(newSubject));
  }),

  // Update subject
  rest.put(`${API_BASE_URL}/api/v1/subjects/:id`, async (req, res, ctx) => {
    await delay(400);
    
    const { id } = req.params;
    const body = await req.json();
    const subjectIndex = mockSubjects.findIndex(s => s.id === parseInt(id as string));
    
    if (subjectIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Subject not found' })
      );
    }
    
    mockSubjects[subjectIndex] = {
      ...mockSubjects[subjectIndex],
      ...body,
      updated_at: new Date().toISOString(),
    };
    
    return res(ctx.status(200), ctx.json(mockSubjects[subjectIndex]));
  }),

  // Delete subject
  rest.delete(`${API_BASE_URL}/api/v1/subjects/:id`, async (req, res, ctx) => {
    await delay(300);
    
    const { id } = req.params;
    const subjectIndex = mockSubjects.findIndex(s => s.id === parseInt(id as string));
    
    if (subjectIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Subject not found' })
      );
    }
    
    mockSubjects.splice(subjectIndex, 1);
    
    return res(ctx.status(204));
  }),

  // ============================================================================
  // TEACHERS API
  // ============================================================================
  
  // Get all teachers
  rest.get(`${API_BASE_URL}/api/v1/teachers`, async (req, res, ctx) => {
    await delay(300);
    
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const search = url.searchParams.get('search') || '';
    const isActive = url.searchParams.get('is_active');
    
    const filtered = filterData(mockTeachers, search, isActive === 'true');
    const result = paginate(filtered, page, limit);
    
    return res(ctx.status(200), ctx.json(result));
  }),

  // Get teacher by ID
  rest.get(`${API_BASE_URL}/api/v1/teachers/:id`, async (req, res, ctx) => {
    await delay(200);
    
    const { id } = req.params;
    const teacher = mockTeachers.find(t => t.id === parseInt(id as string));
    
    if (!teacher) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Teacher not found' })
      );
    }
    
    return res(ctx.status(200), ctx.json(teacher));
  }),

  // Create teacher
  rest.post(`${API_BASE_URL}/api/v1/teachers`, async (req, res, ctx) => {
    await delay(400);
    
    const body = await req.json();
    const newTeacher = {
      id: Math.max(...mockTeachers.map(t => t.id)) + 1,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    mockTeachers.push(newTeacher);
    
    return res(ctx.status(201), ctx.json(newTeacher));
  }),

  // Update teacher
  rest.put(`${API_BASE_URL}/api/v1/teachers/:id`, async (req, res, ctx) => {
    await delay(400);
    
    const { id } = req.params;
    const body = await req.json();
    const teacherIndex = mockTeachers.findIndex(t => t.id === parseInt(id as string));
    
    if (teacherIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Teacher not found' })
      );
    }
    
    mockTeachers[teacherIndex] = {
      ...mockTeachers[teacherIndex],
      ...body,
      updated_at: new Date().toISOString(),
    };
    
    return res(ctx.status(200), ctx.json(mockTeachers[teacherIndex]));
  }),

  // Delete teacher
  rest.delete(`${API_BASE_URL}/api/v1/teachers/:id`, async (req, res, ctx) => {
    await delay(300);
    
    const { id } = req.params;
    const teacherIndex = mockTeachers.findIndex(t => t.id === parseInt(id as string));
    
    if (teacherIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Teacher not found' })
      );
    }
    
    mockTeachers.splice(teacherIndex, 1);
    
    return res(ctx.status(204));
  }),

  // ============================================================================
  // CLASS GROUPS API
  // ============================================================================
  
  // Get all class groups
  rest.get(`${API_BASE_URL}/api/v1/class-groups`, async (req, res, ctx) => {
    await delay(300);
    
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const search = url.searchParams.get('search') || '';
    const isActive = url.searchParams.get('is_active');
    
    const filtered = filterData(mockClassGroups, search, isActive === 'true');
    const result = paginate(filtered, page, limit);
    
    return res(ctx.status(200), ctx.json(result));
  }),

  // Get class group by ID
  rest.get(`${API_BASE_URL}/api/v1/class-groups/:id`, async (req, res, ctx) => {
    await delay(200);
    
    const { id } = req.params;
    const classGroup = mockClassGroups.find(c => c.id === parseInt(id as string));
    
    if (!classGroup) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Class group not found' })
      );
    }
    
    return res(ctx.status(200), ctx.json(classGroup));
  }),

  // Create class group
  rest.post(`${API_BASE_URL}/api/v1/class-groups`, async (req, res, ctx) => {
    await delay(400);
    
    const body = await req.json();
    const newClassGroup = {
      id: Math.max(...mockClassGroups.map(c => c.id)) + 1,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    mockClassGroups.push(newClassGroup);
    
    return res(ctx.status(201), ctx.json(newClassGroup));
  }),

  // Update class group
  rest.put(`${API_BASE_URL}/api/v1/class-groups/:id`, async (req, res, ctx) => {
    await delay(400);
    
    const { id } = req.params;
    const body = await req.json();
    const classGroupIndex = mockClassGroups.findIndex(c => c.id === parseInt(id as string));
    
    if (classGroupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Class group not found' })
      );
    }
    
    mockClassGroups[classGroupIndex] = {
      ...mockClassGroups[classGroupIndex],
      ...body,
      updated_at: new Date().toISOString(),
    };
    
    return res(ctx.status(200), ctx.json(mockClassGroups[classGroupIndex]));
  }),

  // Delete class group
  rest.delete(`${API_BASE_URL}/api/v1/class-groups/:id`, async (req, res, ctx) => {
    await delay(300);
    
    const { id } = req.params;
    const classGroupIndex = mockClassGroups.findIndex(c => c.id === parseInt(id as string));
    
    if (classGroupIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Class group not found' })
      );
    }
    
    mockClassGroups.splice(classGroupIndex, 1);
    
    return res(ctx.status(204));
  }),

  // ============================================================================
  // ROOMS API
  // ============================================================================
  
  // Get all rooms
  rest.get(`${API_BASE_URL}/api/v1/rooms`, async (req, res, ctx) => {
    await delay(300);
    
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const search = url.searchParams.get('search') || '';
    const isActive = url.searchParams.get('is_active');
    
    const filtered = filterData(mockRooms, search, isActive === 'true');
    const result = paginate(filtered, page, limit);
    
    return res(ctx.status(200), ctx.json(result));
  }),

  // Get room by ID
  rest.get(`${API_BASE_URL}/api/v1/rooms/:id`, async (req, res, ctx) => {
    await delay(200);
    
    const { id } = req.params;
    const room = mockRooms.find(r => r.id === parseInt(id as string));
    
    if (!room) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Room not found' })
      );
    }
    
    return res(ctx.status(200), ctx.json(room));
  }),

  // Create room
  rest.post(`${API_BASE_URL}/api/v1/rooms`, async (req, res, ctx) => {
    await delay(400);
    
    const body = await req.json();
    const newRoom = {
      id: Math.max(...mockRooms.map(r => r.id)) + 1,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    mockRooms.push(newRoom);
    
    return res(ctx.status(201), ctx.json(newRoom));
  }),

  // Update room
  rest.put(`${API_BASE_URL}/api/v1/rooms/:id`, async (req, res, ctx) => {
    await delay(400);
    
    const { id } = req.params;
    const body = await req.json();
    const roomIndex = mockRooms.findIndex(r => r.id === parseInt(id as string));
    
    if (roomIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Room not found' })
      );
    }
    
    mockRooms[roomIndex] = {
      ...mockRooms[roomIndex],
      ...body,
      updated_at: new Date().toISOString(),
    };
    
    return res(ctx.status(200), ctx.json(mockRooms[roomIndex]));
  }),

  // Delete room
  rest.delete(`${API_BASE_URL}/api/v1/rooms/:id`, async (req, res, ctx) => {
    await delay(300);
    
    const { id } = req.params;
    const roomIndex = mockRooms.findIndex(r => r.id === parseInt(id as string));
    
    if (roomIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Room not found' })
      );
    }
    
    mockRooms.splice(roomIndex, 1);
    
    return res(ctx.status(204));
  }),

  // ============================================================================
  // ERROR SIMULATION HANDLERS
  // ============================================================================
  
  // Simulate server errors for testing
  rest.get(`${API_BASE_URL}/api/v1/test/500`, async (req, res, ctx) => {
    await delay(100);
    return res(
      ctx.status(500),
      ctx.json({ detail: 'Internal server error' })
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/test/timeout`, async (req, res, ctx) => {
    await delay(30000); // 30 second timeout
    return res(ctx.status(200), ctx.json({ message: 'Success' }));
  }),

  rest.get(`${API_BASE_URL}/api/v1/test/network-error`, (req, res, ctx) => {
    return res.networkError('Network connection failed');
  }),

  // ============================================================================
  // UTILITY HANDLERS
  // ============================================================================
  
  // Health check
  rest.get(`${API_BASE_URL}/health`, async (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        version: '1.0.0',
      })
    );
  }),

  // Reset mock data (for testing)
  rest.post(`${API_BASE_URL}/api/v1/test/reset`, async (req, res, ctx) => {
    mockSubjects = generateMockSubjects(50);
    mockTeachers = generateMockTeachers(30);
    mockClassGroups = generateMockClassGroups(20);
    mockRooms = generateMockRooms(25);
    
    return res(
      ctx.status(200),
      ctx.json({ message: 'Mock data reset successfully' })
    );
  }),
];

export { mockSubjects, mockTeachers, mockClassGroups, mockRooms };