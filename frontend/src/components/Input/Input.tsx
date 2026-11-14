import './Input.css'

export interface InputProps {
    type: string;
    name: string;
    placeholder: string;
    value?: string,
    id: string;
}

const Input = ({ type, name, placeholder, value, id }: InputProps) => {
    return (
        <input
            type={ type }
            name={ name }
            placeholder={ placeholder }
            value={ value || "" }
            id={ id }
            className="form-line-input"
        />
    );
};

export default Input;
