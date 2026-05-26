/**
 * Page Schools : liste de toutes les écoles + create + delete.
 * Pas de filter school_id (Schools est le tenant racine).
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { School } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function Schools() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { setCurrentId, currentId } = useCurrentSchool();

  const { data: schools, isLoading } = useQuery({
    queryKey: ["schools"],
    queryFn: () => api.schools.list(),
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", default_language: "he" });

  const create = useMutation({
    mutationFn: () => api.schools.create(form),
    onSuccess: (school) => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["schools"] });
      setCurrentId(school.id);
      setModalOpen(false);
      setForm({ code: "", name: "", default_language: "he" });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.schools.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["schools"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.schools")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {schools?.length ?? 0} {t("nav.schools")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<School>
            data={schools}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              {
                key: "active",
                label: "",
                width: "60px",
                render: (r) =>
                  r.id === currentId ? (
                    <Badge variant="success">●</Badge>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setCurrentId(r.id)}
                      className="text-xs text-primary-600 hover:underline"
                    >
                      בחר
                    </button>
                  ),
              },
              { key: "code", label: "Code", width: "20%" },
              { key: "name", label: "Nom / שם" },
              { key: "default_language", label: "Lang", width: "10%" },
            ]}
          />
        </CardBody>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")}>
        <ModalBody>
          <div className="space-y-3">
            <Input label="Nom *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input
              label="Code * (kebab-case)"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value.toLowerCase() })}
              hint="amit-netanya"
            />
            <Select
              label="Langue par défaut"
              value={form.default_language}
              onChange={(e) => setForm({ ...form, default_language: e.target.value })}
              options={[
                { value: "he", label: "עברית" },
                { value: "fr", label: "Français" },
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
