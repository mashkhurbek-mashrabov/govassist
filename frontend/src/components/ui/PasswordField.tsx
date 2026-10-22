import { useState } from "react";
import { useTranslation } from "react-i18next";
import { TextField, type TextFieldProps } from "./TextField";

/**
 * Password input with a show/hide toggle.
 *
 * @param props Same as {@link TextField}; `type` is managed here.
 * @returns The field.
 */
export function PasswordField(props: Omit<TextFieldProps, "type" | "children">) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  return (
    <TextField {...props} type={visible ? "text" : "password"}>
      <button
        type="button"
        className="min-h-11 min-w-11 px-2"
        aria-pressed={visible}
        onClick={() => setVisible((value) => !value)}
      >
        {visible ? t("auth.fields.hidePassword") : t("auth.fields.showPassword")}
      </button>
    </TextField>
  );
}
