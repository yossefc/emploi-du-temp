import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { Teacher } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function Teachers() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: teachers, isLoading } = useQuery({
    queryKey: ["teachers", schoolId],
    queryFn: () => api.teachers.list(schoolId!),
    enabled: schoolId !== null,
  });

  const { data: subjects } = useQuery({
    queryKey: ["subjects", schoolId],
    queryFn: () => api.subjects.list(schoolId!),
    enabled: schoolId !== null,
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    code: "",
    first_name: "",
    last_name: "",
    email: "",
    languages: "fr,he",
    qualified_subject_codes: "",
  });

  const create = useMutation({
    mutationFn: async () => {
      if (!schoolId) throw new Error("No school");
      const subjIds = form.qualified_subject_codes
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean)
        .map((code) => subjects?.find((s) => s.code === code)?.id)
        .filter((x): x is number => typeof x === "number");
      return api.teachers.create({
        school_id: schoolId,
        code: form.code,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email || null,
        phone: null,
        max_hours_per_week: null,
        max_hours_per_day: null,
        languages: form.languages.split(",").map((s) => s.trim()).filter(Boolean),
        is_active: true,
        qualified_subject_ids: subjIds,
      });
    },
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["teachers", schoolId] });
      setModalOpen(false);
      setForm({ code: "", first_name: "", last_name: "", email: "", languages: "fr,he", qualified_subject_codes: "" });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.teachers.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["teachers", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.teachers")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {teachers?.length ?? 0} {t("nav.teachers")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<Teacher>
            data={teachers}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              { key: "code", label: t("columns.code"), width: "12%" },
              { key: "name", label: t("columns.name"), render: (r) => `${r.first_name} ${r.last_name}` },
              { key: "email", label: t("columns.email"), render: (r) => r.email ?? "—" },
              {
                key: "languages",
                label: t("columns.languages"),
                render: (r) => (
                  <div className="flex gap-1 flex-wrap">
                    {(r.languages ?? []).map((l) => (
                      <Badge key={l} variant="info">{l}</Badge>
                    ))}
                  </div>
                ),
              },
              {
                key: "subjects",
                label: t("columns.subjects"),
                render: (r) => (
                  <div className="flex gap-1 flex-wrap">
                    {r.qualified_subject_ids.map((id) => {
                      const s = subjects?.find((x) => x.id === id);
                      return (
                        <Badge key={id} variant="default">
                          {s?.name_he ?? s?.code ?? `#${id}`}
                        </Badge>
                      );
                    })}
                  </div>
                ),
              },
            ]}
          />
        </CardBody>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")}>
        <ModalBody>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            <Input label="Prénom *" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
            <Input label="Nom *" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <Input
              label="שפות / Langues (csv)"
              value={form.languages}
              onChange={(e) => setForm({ ...form, languages: e.target.value })}
              hint="fr,he"
            />
            <Input
              label="מקצועות (codes csv)"
              value={form.qualified_subject_codes}
              onChange={(e) => setForm({ ...form, qualified_subject_codes: e.target.value })}
              hint={(subjects ?? []).map((s) => s.code).join(", ")}
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
