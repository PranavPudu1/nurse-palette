export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      day_off_requests: {
        Row: {
          created_at: string
          decided_at: string | null
          end_date: string
          id: string
          nurse_id: string
          reason: string | null
          start_date: string
          status: string
        }
        Insert: {
          created_at?: string
          decided_at?: string | null
          end_date: string
          id?: string
          nurse_id: string
          reason?: string | null
          start_date: string
          status?: string
        }
        Update: {
          created_at?: string
          decided_at?: string | null
          end_date?: string
          id?: string
          nurse_id?: string
          reason?: string | null
          start_date?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "day_off_requests_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "day_off_requests_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
        ]
      }
      managers: {
        Row: {
          created_at: string
          id: string
        }
        Insert: {
          created_at?: string
          id: string
        }
        Update: {
          created_at?: string
          id?: string
        }
        Relationships: []
      }
      nurse_exclusions: {
        Row: {
          created_at: string
          id: string
          nurse_id_1: string
          nurse_id_2: string
          reason: string | null
        }
        Insert: {
          created_at?: string
          id?: string
          nurse_id_1: string
          nurse_id_2: string
          reason?: string | null
        }
        Update: {
          created_at?: string
          id?: string
          nurse_id_1?: string
          nurse_id_2?: string
          reason?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "nurse_exclusions_nurse_id_1_fkey"
            columns: ["nurse_id_1"]
            isOneToOne: false
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "nurse_exclusions_nurse_id_1_fkey"
            columns: ["nurse_id_1"]
            isOneToOne: false
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "nurse_exclusions_nurse_id_2_fkey"
            columns: ["nurse_id_2"]
            isOneToOne: false
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "nurse_exclusions_nurse_id_2_fkey"
            columns: ["nurse_id_2"]
            isOneToOne: false
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
        ]
      }
      nurse_preferences: {
        Row: {
          created_at: string
          id: string
          notes: string | null
          nurse_id: string
          prefers_night: boolean
          prefers_weekday: boolean
          prefers_weekend: boolean
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: string
          notes?: string | null
          nurse_id: string
          prefers_night?: boolean
          prefers_weekday?: boolean
          prefers_weekend?: boolean
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          notes?: string | null
          nurse_id?: string
          prefers_night?: boolean
          prefers_weekday?: boolean
          prefers_weekend?: boolean
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "nurse_preferences_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: true
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "nurse_preferences_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: true
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
        ]
      }
      nurse_unavailability: {
        Row: {
          created_at: string
          date: string
          id: string
          nurse_id: string
          reason: string | null
        }
        Insert: {
          created_at?: string
          date: string
          id?: string
          nurse_id: string
          reason?: string | null
        }
        Update: {
          created_at?: string
          date?: string
          id?: string
          nurse_id?: string
          reason?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "nurse_unavailability_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "nurse_unavailability_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
        ]
      }
      nurses: {
        Row: {
          created_at: string
          department: string | null
          email: string | null
          id: string
          invite_status: string
          level: number
          name: string
          phone: string | null
          updated_at: string
          user_id: string | null
        }
        Insert: {
          created_at?: string
          department?: string | null
          email?: string | null
          id?: string
          invite_status?: string
          level?: number
          name: string
          phone?: string | null
          updated_at?: string
          user_id?: string | null
        }
        Update: {
          created_at?: string
          department?: string | null
          email?: string | null
          id?: string
          invite_status?: string
          level?: number
          name?: string
          phone?: string | null
          updated_at?: string
          user_id?: string | null
        }
        Relationships: []
      }
      schedule_generations: {
        Row: {
          created_at: string
          created_by: string | null
          id: string
          month: number
          options: Json
          year: number
        }
        Insert: {
          created_at?: string
          created_by?: string | null
          id?: string
          month: number
          options: Json
          year: number
        }
        Update: {
          created_at?: string
          created_by?: string | null
          id?: string
          month?: number
          options?: Json
          year?: number
        }
        Relationships: []
      }
      schedules: {
        Row: {
          created_at: string
          date: string
          id: string
          nurse_id: string
          shift_type: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          date: string
          id?: string
          nurse_id: string
          shift_type?: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          date?: string
          id?: string
          nurse_id?: string
          shift_type?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "schedules_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "schedules_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
        ]
      }
      scheduling_constraints: {
        Row: {
          consec_trigger: number
          created_at: string
          days_off_after_consec: number
          days_off_after_night_block: number
          department: string
          id: string
          max_consecutive_workdays: number
          max_shifts_per_day: number
          night_window_k: number
          night_window_max: number
          updated_at: string
        }
        Insert: {
          consec_trigger?: number
          created_at?: string
          days_off_after_consec?: number
          days_off_after_night_block?: number
          department?: string
          id?: string
          max_consecutive_workdays?: number
          max_shifts_per_day?: number
          night_window_k?: number
          night_window_max?: number
          updated_at?: string
        }
        Update: {
          consec_trigger?: number
          created_at?: string
          days_off_after_consec?: number
          days_off_after_night_block?: number
          department?: string
          id?: string
          max_consecutive_workdays?: number
          max_shifts_per_day?: number
          night_window_k?: number
          night_window_max?: number
          updated_at?: string
        }
        Relationships: []
      }
      soft_constraints: {
        Row: {
          constraint_type: string
          created_at: string
          department: string
          id: string
          nurse_id: string | null
          params: Json
        }
        Insert: {
          constraint_type: string
          created_at?: string
          department?: string
          id?: string
          nurse_id?: string | null
          params?: Json
        }
        Update: {
          constraint_type?: string
          created_at?: string
          department?: string
          id?: string
          nurse_id?: string | null
          params?: Json
        }
        Relationships: [
          {
            foreignKeyName: "soft_constraints_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "soft_constraints_nurse_id_fkey"
            columns: ["nurse_id"]
            isOneToOne: false
            referencedRelation: "nurses_public"
            referencedColumns: ["id"]
          },
        ]
      }
      ward_shift_config: {
        Row: {
          created_at: string
          department: string
          id: string
          level_mix: Json
          required_nurses: number
          shift_type: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          department?: string
          id?: string
          level_mix?: Json
          required_nurses?: number
          shift_type: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          department?: string
          id?: string
          level_mix?: Json
          required_nurses?: number
          shift_type?: string
          updated_at?: string
        }
        Relationships: []
      }
    }
    Views: {
      nurses_public: {
        Row: {
          department: string | null
          id: string | null
          invite_status: string | null
          name: string | null
          user_id: string | null
        }
        Insert: {
          department?: string | null
          id?: string | null
          invite_status?: string | null
          name?: string | null
          user_id?: string | null
        }
        Update: {
          department?: string | null
          id?: string | null
          invite_status?: string | null
          name?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      can_read_schedule_for_department: {
        Args: { _nurse_id: string }
        Returns: boolean
      }
      get_department_nurses: {
        Args: never
        Returns: {
          department: string
          id: string
          name: string
        }[]
      }
      is_accepted_nurse: { Args: { _user_id: string }; Returns: boolean }
      is_manager: { Args: never; Returns: boolean }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
