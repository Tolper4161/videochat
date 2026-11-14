import ButtonIcon from "../../ButtonIcon/ButtonIcon";

interface NavbarButtonDataProps {
    icon: string
}

interface NavbarButtonsListProps {
    className: string,
    btnPostfixClassName: string,
    data: NavbarButtonDataProps[]
}

const NavbarButtonsList = ({ className, btnPostfixClassName, data }: NavbarButtonsListProps) => {
    return (
        <ul className={ `nav-btn-list ${className}` }>
            {
                data.map((btnData: NavbarButtonDataProps) => (
                    <li className="nav-list-item btn-list-item">
                        <ButtonIcon icon={ btnData.icon } className={ btnPostfixClassName }  />
                    </li>
                ))
            }
        </ul>
    );
};

export default NavbarButtonsList;
