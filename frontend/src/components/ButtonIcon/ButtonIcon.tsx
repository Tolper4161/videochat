export interface ButtonIconProps {
    className?: string,
    icon: string
}

const ButtonIcon = ({ className="", icon }: ButtonIconProps) => {
    return (
        <button className={ `btn-icon icon ${ icon } ${ className }` }></button>
    );
};

export default ButtonIcon;
