import { useState } from "react"
import { useParams, useNavigate } from "react-router"
import { toast } from "sonner"
import { useCreateObservation } from "@/hooks/use-mutations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { CreateObservationRequest } from "@/types/api"

const PRESETS = [
  { code: "8480-6", display: "BP Systolic", unit: "mmHg" },
  { code: "8462-4", display: "BP Diastolic", unit: "mmHg" },
  { code: "8867-4", display: "Heart Rate", unit: "bpm" },
  { code: "8310-5", display: "Body Temperature", unit: "C" },
]

const today = new Date().toISOString().split("T")[0]

interface FormData {
  code: string
  display: string
  value: string
  unit: string
  effective_date: string
}

interface FormErrors {
  code?: string
  display?: string
  value?: string
}

export function ObservationFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const createObservation = useCreateObservation()

  const [formData, setFormData] = useState<FormData>({
    code: "",
    display: "",
    value: "",
    unit: "",
    effective_date: today,
  })

  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  function validateForm(): boolean {
    const newErrors: FormErrors = {}

    if (!formData.code.trim()) {
      newErrors.code = "Code is required"
    }
    if (!formData.display.trim()) {
      newErrors.display = "Display is required"
    }
    if (!formData.value.trim()) {
      newErrors.value = "Value is required"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handlePresetClick(preset: (typeof PRESETS)[number]) {
    setFormData((prev) => ({
      ...prev,
      code: preset.code,
      display: preset.display,
      unit: preset.unit,
    }))
    setErrors({})
    setSubmitError(null)
  }

  function handleInputChange(
    e: React.ChangeEvent<HTMLInputElement>,
    field: keyof FormData
  ) {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }))
    setErrors((prev) => ({ ...prev, [field]: undefined }))
    setSubmitError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!validateForm()) return

    const payload: CreateObservationRequest = {
      patient_id: id!,
      code: formData.code.trim(),
      display: formData.display.trim(),
      value: formData.value.trim(),
      ...(formData.unit.trim() && { unit: formData.unit.trim() }),
      ...(formData.effective_date && { effective_date: formData.effective_date }),
    }

    try {
      await createObservation.mutateAsync(payload)
      toast.success("Observation created successfully")
      navigate(`/patients/${id}`)
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Failed to create observation"
      )
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>New Observation</CardTitle>
          <p className="text-sm text-muted-foreground">
            Patient ID: {id}
          </p>
        </CardHeader>
        <CardContent>
          <div className="mb-6">
            <Label className="mb-2 block">Quick Select</Label>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((preset) => (
                <Button
                  key={preset.code}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handlePresetClick(preset)}
                >
                  {preset.display}
                </Button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="code">Code *</Label>
              <Input
                id="code"
                value={formData.code}
                onChange={(e) => handleInputChange(e, "code")}
                placeholder="e.g., 8480-6"
                aria-invalid={!!errors.code}
              />
              {errors.code && (
                <p className="text-sm text-destructive">{errors.code}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="display">Display *</Label>
              <Input
                id="display"
                value={formData.display}
                onChange={(e) => handleInputChange(e, "display")}
                placeholder="e.g., BP Systolic"
                aria-invalid={!!errors.display}
              />
              {errors.display && (
                <p className="text-sm text-destructive">{errors.display}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="value">Value *</Label>
              <Input
                id="value"
                value={formData.value}
                onChange={(e) => handleInputChange(e, "value")}
                placeholder="e.g., 120"
                aria-invalid={!!errors.value}
              />
              {errors.value && (
                <p className="text-sm text-destructive">{errors.value}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit">Unit (optional)</Label>
              <Input
                id="unit"
                value={formData.unit}
                onChange={(e) => handleInputChange(e, "unit")}
                placeholder="e.g., mmHg"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="effective_date">Effective Date (optional)</Label>
              <Input
                id="effective_date"
                type="date"
                value={formData.effective_date}
                onChange={(e) => handleInputChange(e, "effective_date")}
              />
            </div>

            {submitError && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                {submitError}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={createObservation.isPending}>
                {createObservation.isPending ? "Creating..." : "Create Observation"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/patients/${id}`)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
