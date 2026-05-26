import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { Group, GroupType as GT } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { MultiSelect } from "@/components/ui/MultiSelect";
import { Badge } from "@/components/ui/Badge";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function Groups() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: groups, isLoading } = useQuery({
    queryKey: ["groups", schoolId],
    queryFn: () => api.groups.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: subjects } = useQuery({
    queryKey: ["subjects", schoolId],
    queryFn: () => api.subjects.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: teachers } = useQuery({
    queryKey: ["teachers", schoolId],
    queryFn: () => api.teachers.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: classes } = useQuery({
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
    label: "",
    grade_id: "",
    subject_id: "",
    hours_per_week: 2,
    group_type: "whole_class" as GT,
    teacher_ids: [] as number[],
    source_class_ids: [] as number[],
  });

  const create = useMutation({
    mutationFn: async () => {
      if (!schoolId) throw new Error("No school");
      if (!form.grade_id || !form.subject_id) throw new Error("Niveau + Matière requis");
      return api.groups.create({
        school_id: schoolId,
        grade_id: Number(form.grade_id),
        subject_id: Number(form.subject_id),
        label: form.label,
        hours_per_week: form.hours_per_week,
        group_type: form.group_type,
        student_count: null,
        parallel_cohort_id: null,
        teacher_ids: form.teacher_ids,
        source_class_ids: form.source_class_ids,
      });
    },
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["groups", schoolId] });
      setModalOpen(false);
      setForm({ label: "", grade_id: "", subject_id: "", hours_per_week: 2,
                 group_type: "whole_class" as GT, teacher_ids: [], source_class_ids: [] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.groups.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["groups", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.groups")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {groups?.length ?? 0} {t("nav.groups")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<Group>
            data={groups}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              { key: "label", label: t("columns.label") },
              {
                key: "subject",
                label: t("nav.subjects"),
                render: (r) => {
                  const s = subjects?.find((x) => x.id === r.subject_id);
                  return (
                    <Badge variant="default">
                      <span style={{ color: s?.color_hex ?? undefined }}>● </span>
                      {s?.name_he ?? s?.code ?? `#${r.subject_id}`}
                    </Badge>
                  );
                },
                width: "15%",
              },
              {
                key: "grade",
                label: t("columns.grade"),
                render: (r) => grades?.find((g) => g.id === r.grade_id)?.name ?? `#${r.grade_id}`,
                width: "10%",
              },
              { key: "hours_per_week", label: t("columns.hours_per_week"), width: "10%" },
              {
                key: "teachers",
                label: t("nav.teachers"),
                render: (r) => (
                  <div className="flex gap-1 flex-wrap">
                    {r.teacher_ids.map((id) => {
                      const teacher = teachers?.find((x) => x.id === id);
                      return (
                        <Badge key={id} variant="default">
                          {teacher?.code ?? `#${id}`}
                        </Badge>
                      );
                    })}
                  </div>
                ),
              },
              {
                key: "classes",
                label: t("nav.classes"),
                render: (r) => (
                  <div className="flex gap-1 flex-wrap">
                    {r.source_class_ids.map((id) => {
                      const cls = classes?.find((x) => x.id === id);
                      return (
                        <Badge key={id} variant="default">
                          {cls?.code ?? `#${id}`}
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

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")} size="lg">
        <ModalBody>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input label="Label *" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} hint="Math 7-1" />
            <Input
              label="h/sem *"
              type="number"
              min={1}
              max={40}
              value={form.hours_per_week}
              onChange={(e) => setForm({ ...form, hours_per_week: Number(e.target.value) })}
            />
            <Select
              label={t("nav.grades") + " *"}
              value={form.grade_id}
              onChange={(e) => setForm({ ...form, grade_id: e.target.value })}
              options={[{ value: "", label: "—" }, ...(grades ?? []).map((g) => ({ value: g.id, label: g.name }))]}
            />
            <Select
              label={t("nav.subjects") + " *"}
              value={form.subject_id}
              onChange={(e) => setForm({ ...form, subject_id: e.target.value })}
              options={[{ value: "", label: "—" }, ...(subjects ?? []).map((s) => ({ value: s.id, label: `${s.code} - ${s.name_he || s.name_fr}` }))]}
            />
            <Select
              label="Type"
              value={form.group_type}
              onChange={(e) => setForm({ ...form, group_type: e.target.value as GT })}
              options={[
                { value: "whole_class", label: "כיתה / Classe entière" },
                { value: "level_group", label: "הקבצה / Niveau" },
                { value: "option_group", label: "אופציה / Option" },
                { value: "gender_group", label: "מגדר / Genre" },
                { value: "split_group", label: "פיצול / Dédoublement" },
              ]}
            />
            <div /> {/* spacer */}
            <MultiSelect
              label={t("nav.teachers")}
              options={(teachers ?? []).map((t) => ({ value: t.id, label: `${t.code} ${t.first_name} ${t.last_name}` }))}
              selected={form.teacher_ids}
              onChange={(ids) => setForm({ ...form, teacher_ids: ids })}
            />
            <MultiSelect
              label={t("nav.classes")}
              options={(classes ?? []).map((c) => ({ value: c.id, label: c.code }))}
              selected={form.source_class_ids}
              onChange={(ids) => setForm({ ...form, source_class_ids: ids })}
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
