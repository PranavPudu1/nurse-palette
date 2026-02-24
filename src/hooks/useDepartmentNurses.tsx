import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";

export interface DepartmentNurse {
  id: string;
  name: string;
  department: string | null;
}

export function useDepartmentNurses() {
  return useQuery<DepartmentNurse[]>({
    queryKey: ["department-nurses"],
    queryFn: async () => {
      const { data, error } = await supabase.rpc("get_department_nurses");
      if (error) throw error;
      return data ?? [];
    },
  });
}
