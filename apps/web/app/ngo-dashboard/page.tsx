"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function NGODashboardPage() {
  const router = useRouter();
  useEffect(() => { router.replace("/ngo/dashboard"); }, [router]);
  return (
    <div className="min-h-screen bg-[#072921] flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-[#115E54] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
