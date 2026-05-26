import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { Room } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function Rooms() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: rooms, isLoading } = useQuery({
    queryKey: ["rooms", schoolId],
    queryFn: () => api.rooms.list(schoolId!),
    enabled: schoolId !== null,
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", capacity: 30, room_type: "" });

  const create = useMutation({
    mutationFn: async () => {
      if (!schoolId) throw new Error("No school");
      return api.rooms.create({
        school_id: schoolId,
        code: form.code,
        name: form.name || form.code,
        capacity: form.capacity,
        room_type: form.room_type || null,
        building: null,
        floor: null,
        equipment: null,
        is_active: true,
      });
    },
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["rooms", schoolId] });
      setModalOpen(false);
      setForm({ code: "", name: "", capacity: 30, room_type: "" });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.rooms.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["rooms", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.rooms")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {rooms?.length ?? 0} {t("nav.rooms")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<Room>
            data={rooms}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              { key: "code", label: "Code", width: "15%" },
              { key: "name", label: "Nom / שם" },
              { key: "capacity", label: "קיבולת / Capacité", width: "15%" },
              { key: "room_type", label: "Type", render: (r) => r.room_type ?? "—", width: "20%" },
            ]}
          />
        </CardBody>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")}>
        <ModalBody>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            <Input label="Nom" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input
              label="קיבולת"
              type="number"
              value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })}
            />
            <Input
              label="Type"
              value={form.room_type}
              onChange={(e) => setForm({ ...form, room_type: e.target.value })}
              hint="lab, gym, classroom…"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setModalOpen(false)}>
            {t("actions.cancel")}
          </Button>
          <Button onClick={() => create.mutate()} loading={create.isPending}>
            {t("actions.create")}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
