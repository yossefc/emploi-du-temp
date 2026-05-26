import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { Subject } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function Subjects() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: subjects, isLoading } = useQuery({
    queryKey: ["subjects", schoolId],
    queryFn: () => api.subjects.list(schoolId!),
    enabled: schoolId !== null,
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    code: "",
    name_fr: "",
    name_he: "",
    color_hex: "#3b82f6",
  });

  const create = useMutation({
    mutationFn: async () => {
      if (!schoolId) throw new Error("No school");
      return api.subjects.create({
        school_id: schoolId,
        code: form.code,
        name_fr: form.name_fr,
        name_he: form.name_he,
        abbreviation: null,
        color_hex: form.color_hex || null,
        required_room_type: null,
        is_religious: false,
        is_active: true,
      });
    },
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["subjects", schoolId] });
      setModalOpen(false);
      setForm({ code: "", name_fr: "", name_he: "", color_hex: "#3b82f6" });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.subjects.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["subjects", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.subjects")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {subjects?.length ?? 0} {t("nav.subjects")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<Subject>
            data={subjects}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              {
                key: "color",
                label: "",
                width: "40px",
                render: (r) => (
                  <div
                    className="h-6 w-6 rounded-full border border-slate-300"
                    style={{ backgroundColor: r.color_hex ?? "#94a3b8" }}
                  />
                ),
              },
              { key: "code", label: t("columns.code"), width: "15%" },
              ...(t("common.language.he", { lng: "he" }) && false ? [] : []),
              // En HE on n'affiche que le nom hébreu
              ...(typeof window !== "undefined" && document.documentElement.lang === "he"
                ? [{ key: "name_he", label: t("columns.name") }]
                : [
                    { key: "name_fr", label: "Nom FR" },
                    { key: "name_he", label: "שם" },
                  ]),
            ]}
          />
        </CardBody>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")}>
        <ModalBody>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            <Input label="Couleur" type="color" value={form.color_hex} onChange={(e) => setForm({ ...form, color_hex: e.target.value })} />
            <Input label="Nom FR *" value={form.name_fr} onChange={(e) => setForm({ ...form, name_fr: e.target.value })} />
            <Input label="שם *" value={form.name_he} onChange={(e) => setForm({ ...form, name_he: e.target.value })} />
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
