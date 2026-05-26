import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { SchoolClass } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function Classes() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: classes, isLoading } = useQuery({
    queryKey: ["classes", schoolId],
    queryFn: () => api.classes.list(schoolId!),
    enabled: schoolId !== null,
  });

  const { data: grades } = useQuery({
    queryKey: ["grades", schoolId],
    queryFn: () => api.grades.list(schoolId!),
    enabled: schoolId !== null,
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    code: "",
    name: "",
    student_count: 25,
    grade_id: "",
  });

  const create = useMutation({
    mutationFn: async () => {
      if (!schoolId) throw new Error("No school");
      if (!form.grade_id) throw new Error("Niveau requis");
      return api.classes.create({
        school_id: schoolId,
        grade_id: Number(form.grade_id),
        code: form.code,
        name: form.name || form.code,
        student_count: form.student_count,
        homeroom_teacher_id: null,
      });
    },
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["classes", schoolId] });
      setModalOpen(false);
      setForm({ code: "", name: "", student_count: 25, grade_id: "" });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.classes.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["classes", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.classes")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {classes?.length ?? 0} {t("nav.classes")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<SchoolClass>
            data={classes}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              { key: "code", label: t("columns.code"), width: "15%" },
              { key: "name", label: t("columns.name") },
              {
                key: "grade",
                label: t("columns.grade"),
                render: (r) => {
                  const g = grades?.find((x) => x.id === r.grade_id);
                  return <Badge variant="info">{g?.name ?? g?.code ?? `#${r.grade_id}`}</Badge>;
                },
              },
              { key: "student_count", label: t("columns.students"), width: "15%" },
            ]}
          />
        </CardBody>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")}>
        <ModalBody>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} hint="7-1" />
            <Input label="Nom" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input
              label="תלמידים"
              type="number"
              value={form.student_count}
              onChange={(e) => setForm({ ...form, student_count: Number(e.target.value) })}
            />
            <Select
              label={t("nav.grades")}
              value={form.grade_id}
              onChange={(e) => setForm({ ...form, grade_id: e.target.value })}
              options={[
                { value: "", label: "—" },
                ...(grades ?? []).map((g) => ({ value: g.id, label: g.name })),
              ]}
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
