import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function Dashboard() {
  const { t } = useTranslation();
  const { data: schools, isLoading } = useQuery({
    queryKey: ["schools"],
    queryFn: () => api.schools.list(),
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          {t("app.title")}
        </h1>
        <p className="mt-1 text-slate-600 dark:text-slate-400">{t("app.tagline")}</p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">{t("nav.schools")}</h2>
        </CardHeader>
        <CardBody>
          {isLoading && <p className="text-slate-500">{t("actions.loading")}</p>}
          {!isLoading && (!schools || schools.length === 0) && (
            <div className="text-center py-8">
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                {t("actions.no_data")}
              </p>
              <Link to="/wizard">
                <Button variant="primary">{t("nav.wizard")} →</Button>
              </Link>
            </div>
          )}
          {schools && schools.length > 0 && (
            <ul className="divide-y divide-slate-200 dark:divide-slate-700">
              {schools.map((s) => (
                <li key={s.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium">{s.name}</p>
                    <p className="text-sm text-slate-500">{s.code}</p>
                  </div>
                  <Link to={`/schedules?school_id=${s.id}`}>
                    <Button variant="ghost" size="sm">
                      {t("nav.schedules")} →
                    </Button>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
