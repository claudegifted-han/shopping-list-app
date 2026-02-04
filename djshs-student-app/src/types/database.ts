export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type UserRole = 'student' | 'teacher' | 'admin'
export type MealType = 'breakfast' | 'lunch' | 'dinner'
export type ApplicationStatus = 'pending' | 'approved' | 'rejected' | 'cancelled' | 'completed'
export type OutingType = 'outing' | 'special_room'
export type DormitoryType = 'today' | 'tomorrow'
export type NotificationType = 'penalty' | 'study' | 'outing' | 'system'

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          student_number: string | null
          name: string
          nickname: string | null
          email: string | null
          alternative_email: string | null
          role: UserRole
          gender: string | null
          phone: string | null
          parent_phone: string | null
          registration_year: number | null
          avatar_url: string | null
          total_penalty: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          student_number?: string | null
          name: string
          nickname?: string | null
          email?: string | null
          alternative_email?: string | null
          role?: UserRole
          gender?: string | null
          phone?: string | null
          parent_phone?: string | null
          registration_year?: number | null
          avatar_url?: string | null
          total_penalty?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          student_number?: string | null
          name?: string
          nickname?: string | null
          email?: string | null
          alternative_email?: string | null
          role?: UserRole
          gender?: string | null
          phone?: string | null
          parent_phone?: string | null
          registration_year?: number | null
          avatar_url?: string | null
          total_penalty?: number
          created_at?: string
          updated_at?: string
        }
      }
      passkeys: {
        Row: {
          id: string
          user_id: string
          credential_id: string
          public_key: string
          counter: number
          device_type: string | null
          browser: string | null
          created_at: string
          last_used_at: string | null
        }
        Insert: {
          id?: string
          user_id: string
          credential_id: string
          public_key: string
          counter?: number
          device_type?: string | null
          browser?: string | null
          created_at?: string
          last_used_at?: string | null
        }
        Update: {
          id?: string
          user_id?: string
          credential_id?: string
          public_key?: string
          counter?: number
          device_type?: string | null
          browser?: string | null
          created_at?: string
          last_used_at?: string | null
        }
      }
      meals: {
        Row: {
          id: string
          date: string
          meal_type: MealType
          menu: string | null
          created_at: string
        }
        Insert: {
          id?: string
          date: string
          meal_type: MealType
          menu?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          date?: string
          meal_type?: MealType
          menu?: string | null
          created_at?: string
        }
      }
      study_seats: {
        Row: {
          id: string
          room_name: string
          seat_number: string
          is_available: boolean
          created_at: string
        }
        Insert: {
          id?: string
          room_name: string
          seat_number: string
          is_available?: boolean
          created_at?: string
        }
        Update: {
          id?: string
          room_name?: string
          seat_number?: string
          is_available?: boolean
          created_at?: string
        }
      }
      study_applications: {
        Row: {
          id: string
          user_id: string
          seat_id: string
          date: string
          status: ApplicationStatus
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          seat_id: string
          date: string
          status?: ApplicationStatus
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          seat_id?: string
          date?: string
          status?: ApplicationStatus
          created_at?: string
          updated_at?: string
        }
      }
      outing_applications: {
        Row: {
          id: string
          user_id: string
          title: string
          description: string | null
          type: OutingType
          start_time: string
          end_time: string
          status: ApplicationStatus
          is_public: boolean
          approved_by: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          description?: string | null
          type: OutingType
          start_time: string
          end_time: string
          status?: ApplicationStatus
          is_public?: boolean
          approved_by?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          description?: string | null
          type?: OutingType
          start_time?: string
          end_time?: string
          status?: ApplicationStatus
          is_public?: boolean
          approved_by?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      dormitory_applications: {
        Row: {
          id: string
          user_id: string
          date: string
          type: DormitoryType
          status: ApplicationStatus
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          date: string
          type: DormitoryType
          status?: ApplicationStatus
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          date?: string
          type?: DormitoryType
          status?: ApplicationStatus
          created_at?: string
          updated_at?: string
        }
      }
      penalty_reasons: {
        Row: {
          id: string
          title: string
          points: number
          category: string | null
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          title: string
          points: number
          category?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          title?: string
          points?: number
          category?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      penalty_records: {
        Row: {
          id: string
          reason_id: string | null
          issued_by: string
          points: number
          description: string | null
          issued_date: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          reason_id?: string | null
          issued_by: string
          points: number
          description?: string | null
          issued_date?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          reason_id?: string | null
          issued_by?: string
          points?: number
          description?: string | null
          issued_date?: string
          created_at?: string
          updated_at?: string
        }
      }
      penalty_record_targets: {
        Row: {
          id: string
          record_id: string
          user_id: string
          created_at: string
        }
        Insert: {
          id?: string
          record_id: string
          user_id: string
          created_at?: string
        }
        Update: {
          id?: string
          record_id?: string
          user_id?: string
          created_at?: string
        }
      }
      notifications: {
        Row: {
          id: string
          user_id: string
          title: string
          message: string | null
          type: NotificationType
          is_read: boolean
          related_id: string | null
          created_at: string
          read_at: string | null
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          message?: string | null
          type: NotificationType
          is_read?: boolean
          related_id?: string | null
          created_at?: string
          read_at?: string | null
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          message?: string | null
          type?: NotificationType
          is_read?: boolean
          related_id?: string | null
          created_at?: string
          read_at?: string | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      user_role: UserRole
      meal_type: MealType
      application_status: ApplicationStatus
      outing_type: OutingType
      dormitory_type: DormitoryType
      notification_type: NotificationType
    }
  }
}

export type Profile = Database['public']['Tables']['profiles']['Row']
export type Passkey = Database['public']['Tables']['passkeys']['Row']
export type Meal = Database['public']['Tables']['meals']['Row']
export type StudySeat = Database['public']['Tables']['study_seats']['Row']
export type StudyApplication = Database['public']['Tables']['study_applications']['Row']
export type OutingApplication = Database['public']['Tables']['outing_applications']['Row']
export type DormitoryApplication = Database['public']['Tables']['dormitory_applications']['Row']
export type PenaltyReason = Database['public']['Tables']['penalty_reasons']['Row']
export type PenaltyRecord = Database['public']['Tables']['penalty_records']['Row']
export type PenaltyRecordTarget = Database['public']['Tables']['penalty_record_targets']['Row']
export type Notification = Database['public']['Tables']['notifications']['Row']

// Extended types with relations
export type StudyApplicationWithDetails = StudyApplication & {
  seat: StudySeat
  user: Profile
}

export type OutingApplicationWithDetails = OutingApplication & {
  user: Profile
  approver?: Profile | null
}

export type PenaltyRecordWithDetails = PenaltyRecord & {
  reason?: PenaltyReason | null
  issuer: Pick<Profile, 'id' | 'name' | 'student_number'>
  targets: Array<Pick<Profile, 'id' | 'name' | 'student_number'>>
}
